# Error Handling with GIFs - Testing Guide

## Overview
The Chatbot component now displays animated GIFs when encountering HTTP errors, specifically designed for 403 (Forbidden) errors and other common HTTP status codes.

## Features Added

### 1. GIF Display for Different Error Types
- **403 Forbidden**: Shows random access denied/forbidden GIFs
- **404 Not Found**: Shows "not found" themed GIF  
- **429 Rate Limit**: Shows "slow down" themed GIF
- **500 Server Error**: Shows server error themed GIF
- **General Errors**: Shows general error GIF

### 2. Enhanced Error Messages
The chatbot provides contextual error messages based on:
- HTTP status code
- Error message content (rate limit, permission, token, etc.)
- User-friendly explanations

### 3. Visual Enhancements
- GIFs are displayed with rounded corners and shadow
- Maximum height of 200px for consistent layout
- Responsive design that works on mobile

## Testing the 403 Error with GIF

### Option 1: Backend Simulation
If you control the FastAPI backend, you can temporarily modify your endpoint to return a 403 error:

```python
@router.post("/extract-info")
async def extract_or_confirm_info(...):
    # Temporarily return 403 for testing
    raise HTTPException(status_code=403, detail="Testing 403 error with GIF")
```

### Option 2: Network Interception
Use browser dev tools to intercept the API call and modify the response:
1. Open Chrome DevTools (F12)
2. Go to Network tab
3. Send a message in the chatbot
4. Right-click on the `/extract-info` request
5. Select "Edit and Resend"
6. Modify the response to return 403

### Option 3: Mock API Response
Temporarily modify the API service to simulate a 403 error:

```typescript
// In api.ts, temporarily add at the start of extractOrConfirmInfo:
throw new ApiError("Access forbidden - testing GIF display", 403);
```

## Expected Behavior

When a 403 error occurs:
1. ✅ Error message displays with appropriate text
2. ✅ Random GIF from the 403 collection is shown
3. ✅ Red error styling is applied to the message bubble
4. ✅ Error icon appears with "Error occurred" text
5. ✅ GIF is properly sized and styled

## GIF Sources
All GIFs are sourced from Giphy and include:
- Access denied animations
- "Computer says no" themes
- Stop signs and barriers
- Humorous error representations

## Customization
To add your own GIFs:
1. Update the `get403ErrorGif()` function with new URLs
2. Add more status codes to `getErrorGif()` function
3. Customize error messages in the switch statement

The implementation is fully type-safe and handles edge cases gracefully.
