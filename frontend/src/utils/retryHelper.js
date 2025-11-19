/**
 * Retry Helper Utilities
 * Provides retry logic with exponential backoff for handling rate limits
 */

/**
 * Sleep/delay function
 * @param {number} ms - Milliseconds to sleep
 */
export const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

/**
 * Retry a function with exponential backoff
 * @param {Function} fn - Async function to retry
 * @param {Object} options - Retry options
 * @param {number} options.maxRetries - Maximum number of retries (default: 3)
 * @param {number} options.initialDelay - Initial delay in ms (default: 1000)
 * @param {number} options.maxDelay - Maximum delay in ms (default: 10000)
 * @param {number} options.backoffMultiplier - Multiplier for exponential backoff (default: 2)
 * @param {Function} options.shouldRetry - Function to determine if error should be retried
 * @returns {Promise} - Result of the function
 */
export const retryWithBackoff = async (fn, options = {}) => {
  const {
    maxRetries = 3,
    initialDelay = 1000,
    maxDelay = 10000,
    backoffMultiplier = 2,
    shouldRetry = (error) => {
      // Default: retry on network errors and 429 (rate limit)
      if (!error.response) return true; // Network error
      const status = error.response?.status;
      return status === 429 || status === 503 || status === 502;
    }
  } = options;

  let lastError;
  let delay = initialDelay;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      // Try to execute the function
      const result = await fn();
      return result;
    } catch (error) {
      lastError = error;

      // Check if we should retry
      if (attempt < maxRetries && shouldRetry(error)) {
        // Log retry attempt
        console.warn(`Attempt ${attempt + 1} failed, retrying in ${delay}ms...`, {
          error: error.message,
          status: error.response?.status
        });

        // Wait before retrying
        await sleep(delay);

        // Increase delay for next retry (exponential backoff)
        delay = Math.min(delay * backoffMultiplier, maxDelay);
      } else {
        // Max retries reached or error is not retryable
        throw lastError;
      }
    }
  }

  // This should never be reached, but just in case
  throw lastError;
};

/**
 * Add random jitter to a delay to prevent thundering herd
 * @param {number} delay - Base delay in ms
 * @param {number} jitterPercent - Jitter percentage (default: 0.3 = 30%)
 */
export const addJitter = (delay, jitterPercent = 0.3) => {
  const jitter = delay * jitterPercent;
  return delay + (Math.random() * jitter * 2 - jitter);
};

/**
 * Rate limiter for batch operations
 * Ensures operations are spread out to avoid hitting rate limits
 */
export class RateLimiter {
  constructor(maxConcurrent = 3, minDelayBetweenRequests = 500) {
    this.maxConcurrent = maxConcurrent;
    this.minDelayBetweenRequests = minDelayBetweenRequests;
    this.queue = [];
    this.activeCount = 0;
    this.lastRequestTime = 0;
  }

  async execute(fn) {
    // Wait if we're at max concurrent requests
    while (this.activeCount >= this.maxConcurrent) {
      await sleep(100);
    }

    // Ensure minimum delay between requests
    const now = Date.now();
    const timeSinceLastRequest = now - this.lastRequestTime;
    if (timeSinceLastRequest < this.minDelayBetweenRequests) {
      await sleep(this.minDelayBetweenRequests - timeSinceLastRequest);
    }

    this.activeCount++;
    this.lastRequestTime = Date.now();

    try {
      const result = await fn();
      return result;
    } finally {
      this.activeCount--;
    }
  }
}
