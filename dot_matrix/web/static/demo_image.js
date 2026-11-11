// The demo face (FaceGenerator.create_test_face, exported by the API) decoded once into RGB pixels.
import { api } from './core.js';
import { fileToRGB } from './image_io.js';

let demo = null;
export function demoImage() {
  if (!demo) demo = api('/demo').then(async d => ({ ...d, img: await fileToRGB(await (await fetch(d.png)).blob()) }));
  return demo;
}
