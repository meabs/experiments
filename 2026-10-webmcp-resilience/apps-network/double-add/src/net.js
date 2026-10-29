// Calls to the shop's servers are sent again if they take too long, so one slow moment doesn't leave the customer
// waiting. withRetry(send) calls send() and, if it has not answered within timeoutMs, calls it again (up to `retries`
// more times). The first answer wins; it rejects only if every attempt failed.
export function withRetry(send, { timeoutMs = 800, retries = 1 } = {}) {
  return new Promise((resolve, reject) => {
    let done = false;
    let started = 0;
    let failed = 0;
    let timer = null;
    const attempt = () => {
      started++;
      send().then(
        (result) => {
          if (done) return;
          done = true;
          clearTimeout(timer);
          resolve(result);
        },
        (error) => {
          failed++;
          if (!done && failed === started && started > retries) {
            done = true;
            reject(error);
          }
        },
      );
      if (started <= retries) timer = setTimeout(attempt, timeoutMs);
    };
    attempt();
  });
}
