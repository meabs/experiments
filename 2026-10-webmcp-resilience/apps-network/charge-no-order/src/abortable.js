// Lets a caller stop waiting for a promise when `signal` aborts: the returned promise rejects with an AbortError at
// once, so a cancelled checkout stops straight away instead of finishing the step it was on.
export function abortable(promise, signal) {
  if (!signal) return promise;
  if (signal.aborted) return Promise.reject(new DOMException('Cancelled', 'AbortError'));
  return new Promise((resolve, reject) => {
    const onAbort = () => reject(new DOMException('Cancelled', 'AbortError'));
    signal.addEventListener('abort', onAbort, { once: true });
    promise.then(
      (value) => { signal.removeEventListener('abort', onAbort); resolve(value); },
      (error) => { signal.removeEventListener('abort', onAbort); reject(error); },
    );
  });
}

export const isAbort = (e) => e?.name === 'AbortError';
