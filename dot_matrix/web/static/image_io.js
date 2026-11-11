// Browser image helpers: decode a File / data URL into RGB pixels for the JS engine, and canvas -> download.
import { makeImage } from './pil_ops.js';

// Decode with EXIF orientation applied (as the local app's server does). Alpha is dropped, like Pillow's RGBA -> RGB.
export async function fileToRGB(blob) {
  const bmp = await createImageBitmap(blob, { imageOrientation: 'from-image' });
  const cv = document.createElement('canvas');
  cv.width = bmp.width; cv.height = bmp.height;
  const ctx = cv.getContext('2d', { willReadFrequently: true });
  ctx.drawImage(bmp, 0, 0);
  const rgba = ctx.getImageData(0, 0, cv.width, cv.height).data, n = cv.width * cv.height, rgb = new Uint8Array(n * 3);
  for (let i = 0; i < n; i++) { rgb[3 * i] = rgba[4 * i]; rgb[3 * i + 1] = rgba[4 * i + 1]; rgb[3 * i + 2] = rgba[4 * i + 2]; }
  bmp.close && bmp.close();
  return makeImage(cv.width, cv.height, 3, rgb);
}

export async function dataUrlToBlob(url) { return (await fetch(url)).blob(); }

export function canvasBlob(cv) { return new Promise(res => cv.toBlob(res, 'image/png')); }
