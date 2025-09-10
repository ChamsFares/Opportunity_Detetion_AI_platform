import axios from 'axios';

export interface ProgressUpdate {
  sessionId: string;
  phase: string;
  percentage: number;
  currentTask: string;
  estimatedTimeRemaining: number;
  elapsedTime: number;
  totalPhases: number;
  currentPhase: number;
}

export interface ProgressPhase {
  name: string;
  description: string;
  estimatedDuration: number; // in seconds
}

export const ANALYSIS_PHASES: ProgressPhase[] = [
  { name: 'Initialization', description: 'Setting up analysis environment', estimatedDuration: 5 },
  { name: 'Data Collection', description: 'Gathering business information', estimatedDuration: 15 },
  { name: 'Market Research', description: 'Analyzing market trends and competitors', estimatedDuration: 30 },
  { name: 'Opportunity Analysis', description: 'Identifying growth opportunities', estimatedDuration: 25 },
  { name: 'Report Generation', description: 'Creating comprehensive report', estimatedDuration: 20 },
  { name: 'Finalization', description: 'Preparing final analysis', estimatedDuration: 5 }
];

export class ProgressTracker {
  private sessionId: string;
  private progressCallback?: (progress: ProgressUpdate) => void;
  private errorCallback?: (error: Error) => void;
  private intervalId?: number;
  private isTracking = false;
  
  constructor(sessionId: string) {
    this.sessionId = sessionId;
  }

  public startTracking(
    progressCallback: (progress: ProgressUpdate) => void,
    errorCallback?: (error: Error) => void
  ) {
    this.progressCallback = progressCallback;
    this.errorCallback = errorCallback;
    this.isTracking = true;

    // Poll backend every 2 seconds for progress updates
    this.intervalId = setInterval(() => {
      this.fetchProgress();
    }, 2000);

    // Initial fetch
    this.fetchProgress();
  }

  public stopTracking() {
    this.isTracking = false;
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = undefined;
    }
  }

  private async fetchProgress() {
    if (!this.isTracking) return;

    try {
      const response = await axios.get(`/api/analysis/progress/${this.sessionId}`);
      const data = response.data;

      if (data.status === 'success' && data.progress) {
        const progressUpdate: ProgressUpdate = {
          sessionId: this.sessionId,
          phase: data.progress.current_phase || 'Unknown',
          percentage: Math.round(data.progress.percentage || 0),
          currentTask: data.progress.current_task || 'Processing...',
          estimatedTimeRemaining: data.progress.estimated_time_remaining || 0,
          elapsedTime: data.progress.elapsed_time || 0,
          totalPhases: ANALYSIS_PHASES.length,
          currentPhase: this.getCurrentPhaseIndex(data.progress.current_phase)
        };

        this.progressCallback?.(progressUpdate);

        // Stop tracking if analysis is complete
        if (progressUpdate.percentage >= 100) {
          this.stopTracking();
        }
      }
    } catch (error) {
      console.error('Failed to fetch progress:', error);
      this.errorCallback?.(error as Error);
    }
  }

  private getCurrentPhaseIndex(phaseName: string): number {
    const index = ANALYSIS_PHASES.findIndex(phase => 
      phase.name.toLowerCase() === phaseName?.toLowerCase()
    );
    return index >= 0 ? index + 1 : 1;
  }

  public static formatTime(seconds: number): string {
    if (seconds <= 0) return '--';
    
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    
    if (minutes > 0) {
      return `${minutes}m ${remainingSeconds}s`;
    } else {
      return `${remainingSeconds}s`;
    }
  }

  public static createSimulatedProgress(
    sessionId: string,
    onProgress: (progress: ProgressUpdate) => void,
    onComplete?: () => void
  ): () => void {
    let currentPhaseIndex = 0;
    let phaseProgress = 0;
    let startTime = Date.now();
    
    const interval = setInterval(() => {
      const currentPhase = ANALYSIS_PHASES[currentPhaseIndex];
      const elapsedTime = Math.floor((Date.now() - startTime) / 1000);
      
      // Calculate overall progress
      const completedPhases = currentPhaseIndex;
      const totalProgress = (completedPhases / ANALYSIS_PHASES.length) + 
                           (phaseProgress / 100 / ANALYSIS_PHASES.length);
      const percentage = Math.min(Math.round(totalProgress * 100), 100);
      
      // Calculate estimated time remaining
      const totalEstimatedTime = ANALYSIS_PHASES.reduce((sum, phase) => sum + phase.estimatedDuration, 0);
      const estimatedTimeRemaining = Math.max(0, totalEstimatedTime - elapsedTime);
      
      const progressUpdate: ProgressUpdate = {
        sessionId,
        phase: currentPhase.name,
        percentage,
        currentTask: currentPhase.description,
        estimatedTimeRemaining,
        elapsedTime,
        totalPhases: ANALYSIS_PHASES.length,
        currentPhase: currentPhaseIndex + 1
      };
      
      onProgress(progressUpdate);
      
      // Update phase progress
      phaseProgress += Math.random() * 8 + 2; // 2-10% per update
      
      if (phaseProgress >= 100) {
        currentPhaseIndex++;
        phaseProgress = 0;
        
        if (currentPhaseIndex >= ANALYSIS_PHASES.length) {
          clearInterval(interval);
          onComplete?.();
          return;
        }
      }
    }, 1000);
    
    return () => clearInterval(interval);
  }
}
