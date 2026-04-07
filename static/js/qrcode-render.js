import QRCode from "qrcode";

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("canvas[data-qr-value]").forEach((canvas) => {
    const value = canvas.dataset.qrValue;
    if (value) {
      QRCode.toCanvas(canvas, value, { width: 200, margin: 2 });
    }
  });
});
