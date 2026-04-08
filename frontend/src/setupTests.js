// jest-dom adds custom jest matchers for asserting on DOM nodes.
// allows you to do things like:
// expect(element).toHaveTextContent(/react/i)
// learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom';
import { TextDecoder, TextEncoder } from 'node:util';

// MUI X DataGrid expects Web APIs in Jest's Node environment
if (globalThis.TextEncoder === undefined) {
  globalThis.TextEncoder = TextEncoder;
}
if (globalThis.TextDecoder === undefined) {
  globalThis.TextDecoder = TextDecoder;
}
