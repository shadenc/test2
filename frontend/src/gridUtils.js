/** Row merge for correction modal — module-level to avoid deep nesting in useEffect. */
export function mergeCorrectionIntoRows(prevRows, updated) {
  return prevRows.map((row) => {
    if (
      row.symbol &&
      updated.company_symbol &&
      row.symbol.toString() === updated.company_symbol.toString()
    ) {
      return {
        ...row,
        retained_earnings: updated.retained_earnings || updated.value || "",
        reinvested_earnings: updated.reinvested_earnings || "",
        year: updated.year || "",
        error: updated.error || "",
      };
    }
    return row;
  });
}

export function quarterLabelFromDateString(dateString) {
  if (!dateString) return "";
  try {
    const date = new Date(dateString);
    const month = date.getMonth() + 1;
    const year = date.getFullYear();
    if (month >= 1 && month <= 3) return `Q1 ${year}`;
    if (month >= 4 && month <= 6) return `Q2 ${year}`;
    if (month >= 7 && month <= 9) return `Q3 ${year}`;
    if (month >= 10 && month <= 12) return `Q4 ${year}`;
    return "";
  } catch {
    return "";
  }
}
