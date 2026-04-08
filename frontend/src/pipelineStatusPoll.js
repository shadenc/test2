const TERMINAL_JOB_STATUSES = new Set(["completed", "idle"]);

function scheduleReloadFns(reloadFns, reloadDelayMs) {
  setTimeout(() => {
    reloadFns.forEach((fn) => fn());
  }, reloadDelayMs);
}

function finishTerminalPoll(
  intervalId,
  setPollId,
  setProgressOpen,
  reloadFns,
  reloadDelayMs,
  onComplete,
) {
  clearInterval(intervalId);
  setPollId(null);
  setProgressOpen(false);
  scheduleReloadFns(reloadFns, reloadDelayMs);
  if (typeof onComplete === "function") {
    onComplete();
  }
}

/**
 * One poll iteration (top-level to satisfy Sonar S2004 nesting limit).
 */
async function runPipelinePollOnce(ctx) {
  const {
    apiUrl,
    statusPath,
    setJobStatus,
    warnMessage,
    intervalId,
    setPollId,
    setProgressOpen,
    reloadFns,
    reloadDelayMs,
    onComplete,
  } = ctx;
  try {
    const res = await fetch(`${apiUrl}${statusPath}`);
    const data = await res.json();
    setJobStatus(data);
    if (!TERMINAL_JOB_STATUSES.has(data.status)) {
      return;
    }
    finishTerminalPoll(
      intervalId,
      setPollId,
      setProgressOpen,
      reloadFns,
      reloadDelayMs,
      onComplete,
    );
  } catch (e) {
    console.warn(warnMessage, e);
  }
}

/**
 * Factory for PDF / net-profit pipeline status polling (deduplicates App.js interval logic).
 * @param {object} opts
 * @param {() => unknown} opts.getPollId
 * @param {(id: number | null) => void} opts.setPollId
 * @param {string} opts.apiUrl
 * @param {string} opts.statusPath
 * @param {(data: object) => void} opts.setJobStatus
 * @param {(open: boolean) => void} opts.setProgressOpen
 * @param {Array<() => void>} opts.reloadFns
 * @param {string} opts.warnMessage
 */
export function createPipelineStatusPoller(opts) {
  const {
    getPollId,
    setPollId,
    apiUrl,
    statusPath,
    setJobStatus,
    setProgressOpen,
    reloadFns,
    warnMessage,
    intervalMs = 1500,
    reloadDelayMs = 300,
  } = opts;

  return function startPoll(onComplete) {
    if (getPollId() != null) return;
    const id = setInterval(() => {
      void runPipelinePollOnce({
        apiUrl,
        statusPath,
        setJobStatus,
        warnMessage,
        intervalId: id,
        setPollId,
        setProgressOpen,
        reloadFns,
        reloadDelayMs,
        onComplete,
      });
    }, intervalMs);
    setPollId(id);
  };
}
