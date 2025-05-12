self.onmessage = function(event) {
  try {
    const result = eval(event.data);
    self.postMessage({ result });
  } catch (e) {
    self.postMessage({ error: e.message });
  }
};