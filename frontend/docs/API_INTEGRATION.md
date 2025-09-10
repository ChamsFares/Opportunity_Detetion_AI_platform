# API Integration Documentation

## Overview

This document describes how to integrate with the OpporTuna FastAPI backend using the provided API service.

## Setup

1. Copy `.env.example` to `.env` and update the `VITE_API_BASE_URL` to point to your backend:
   ```bash
   cp .env.example .env
   ```

2. Update the API base URL in `.env`:
   ```
   VITE_API_BASE_URL=http://localhost:8000
   ```

## API Service Functions

### `extractOrConfirmInfo(prompt, files, sessionId, isConfirmation)`

Main function to extract or confirm business information from user input.

**Parameters:**
- `prompt` (string): User's text input
- `files` (File[] | null): Optional array of uploaded files
- `sessionId` (string | null): Optional session identifier
- `isConfirmation` (boolean): Whether this is a confirmation request

**Returns:** Promise<ApiResponse>

### `processChatbotConversation(messages, files, sessionId)`

Process an entire chatbot conversation to extract business information.

**Parameters:**
- `messages` (Array): Array of conversation messages
- `files` (File[] | null): Optional files
- `sessionId` (string | null): Session identifier

### `generateSessionId()`

Generate a unique session ID for tracking conversations.

**Returns:** string

## Usage in Components

```typescript
import { processChatbotConversation, generateSessionId } from '../services/api';

// In your component
const [sessionId] = useState(() => generateSessionId());

// Process conversation
const result = await processChatbotConversation(messages, files, sessionId);

if (result.status === 'processed' || result.status === 'confirmed') {
  // Success - all information collected
  const businessInfo = result.extracted_info || result.confirmed_info;
  onComplete(businessInfo);
} else if (result.status === 'confirmation_required') {
  // Need more information
  console.log('Missing fields:', result.missing_info);
}
```

## Response Types

### Success Response
```typescript
{
  status: 'processed' | 'confirmed',
  message: string,
  extracted_info?: ExtractedInfo,
  confirmed_info?: ExtractedInfo,
  website_crawled_info?: Record<string, unknown>
}
```

### Confirmation Required Response
```typescript
{
  status: 'confirmation_required',
  message: string,
  extracted_info: ExtractedInfo,
  missing_info: string[],
  newly_provided?: string[]
}
```

## File Upload Support

The API service supports uploading various file types:
- PDF (.pdf)
- Word documents (.doc, .docx)
- Text files (.txt)
- CSV files (.csv)
- Excel files (.xlsx, .xls)

Files are automatically included in the FormData when calling the API.

## Error Handling

The API service includes comprehensive error handling:
- Network errors
- HTTP status errors (403, 400, 500)
- File upload errors
- Validation errors

Always wrap API calls in try-catch blocks for proper error handling.
