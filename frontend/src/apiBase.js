/** Single source for API base URL (avoids circular imports and duplicate literals). */
export const API_URL = process.env.REACT_APP_API_URL || "http://localhost:5003";
