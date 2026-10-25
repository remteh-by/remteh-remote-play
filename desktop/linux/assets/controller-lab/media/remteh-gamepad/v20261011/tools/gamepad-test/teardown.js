const idleTurn = () => new Promise(resolve => setTimeout(resolve, 20));
const settle = operation => {try{return Promise.resolve(operation());}catch(error){return Promise.reject(error);}};

export async function teardownGamepadSession({cancelAuto = () => {}, tuning, lab, actuator, engine} = {}) {
  cancelAuto();
  await Promise.allSettled([
    settle(() => tuning?.dispose?.()),
    settle(() => lab?.stop?.()),
    settle(() => actuator?.reset?.())
  ]);
  if (!engine?.state?.connected) return;
  // Calibration writes and native effect cleanup own the HID transport until
  // their readback/rollback is complete. Closing it earlier can strand a
  // temporary write and leaves the cross-tab lease behind.
  while (engine.state.busy) await idleTurn();
  await engine.disconnect();
}
