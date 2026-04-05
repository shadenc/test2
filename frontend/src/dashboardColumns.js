/**
 * DataGrid column definitions — kept outside App() for lower Sonar cognitive complexity / nesting.
 */
import React from "react";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import Tooltip from "@mui/material/Tooltip";
import IconButton from "@mui/material/IconButton";
import VisibilityIcon from "@mui/icons-material/Visibility";

export const GRID_EMPTY_AR = "لايوجد";

function isEmptyCellValue(value) {
  return !value || value === "" || value === "null" || value === "undefined";
}

function headerPreviousQuarterLabel(quarterFilter) {
  if (quarterFilter === "Q1") return "2024Q4";
  if (quarterFilter === "Q2") return "2025Q1";
  if (quarterFilter === "Q3") return "2025Q2";
  if (quarterFilter === "Q4") return "2025Q3";
  return "2024Q4";
}

function headerCurrentQuarterLabel(quarterFilter) {
  if (quarterFilter === "Q1") return "2025Q1";
  if (quarterFilter === "Q2") return "2025Q2";
  if (quarterFilter === "Q3") return "2025Q3";
  if (quarterFilter === "Q4") return "2025Q4";
  return "2025Q1";
}

function evidenceQuarterForPreviousColumn(quarterFilter) {
  if (quarterFilter === "Q1") return "Annual_2024";
  if (quarterFilter === "Q2") return "Q1_2025";
  if (quarterFilter === "Q3") return "Q2_2025";
  return "Q3_2025";
}

function evidenceQuarterForCurrentColumn(quarterFilter) {
  if (quarterFilter === "Q1") return "Q1_2025";
  if (quarterFilter === "Q2") return "Q2_2025";
  if (quarterFilter === "Q3") return "Q3_2025";
  return "Q4_2025";
}

function signedAmountPrefix(numValue) {
  if (numValue === 0) return "";
  return numValue > 0 ? "+" : "";
}

function SignedSarTypography({ value }) {
  const numValue = Number.parseFloat(value);
  if (Number.isNaN(numValue)) {
    return value;
  }
  const isPositive = numValue >= 0;
  const color = isPositive ? "#2e7d32" : "#d32f2f";
  const sign = signedAmountPrefix(numValue);
  return (
    <Typography sx={{ color, fontWeight: "bold" }}>
      {sign}
      {numValue.toLocaleString("en-US")} SAR
    </Typography>
  );
}

function RetainedValueWithEvidence({ symbol, value, quarterFilter, fetchEvidenceData, evidenceKind }) {
  if (isEmptyCellValue(value)) {
    return GRID_EMPTY_AR;
  }
  const numValue = Number.parseFloat(value);
  if (Number.isNaN(numValue)) {
    return value;
  }
  const evidenceQuarter =
    evidenceKind === "previous"
      ? evidenceQuarterForPreviousColumn(quarterFilter)
      : evidenceQuarterForCurrentColumn(quarterFilter);

  const openEvidence = (e) => {
    e.stopPropagation();
    fetchEvidenceData(symbol, evidenceQuarter);
  };

  return (
    <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
      <Typography>{numValue.toLocaleString("en-US")}</Typography>
      <Tooltip title="عرض دليل الاستخراج - انقر لرؤية المستند الأصلي" arrow placement="top">
        <IconButton
          size="small"
          onClick={openEvidence}
          sx={{
            color: "#1e6641",
            "&:hover": { bgcolor: "#e8f5ee" },
            padding: "8px",
            minWidth: "40px",
            width: "40px",
            height: "40px",
          }}
        >
          <VisibilityIcon sx={{ fontSize: "16px" }} />
        </IconButton>
      </Tooltip>
    </Box>
  );
}

function NetProfitGridCell({ row, quarterFilter, netProfitData }) {
  const companySymbol = row?.company_symbol;
  const companyNetProfit = companySymbol ? netProfitData[companySymbol] : undefined;
  const quarterly = companyNetProfit?.quarterly_net_profit;
  if (!quarterly) {
    return GRID_EMPTY_AR;
  }
  let quarterKey;
  if (quarterFilter === "Q1") quarterKey = "Q1 2025";
  else if (quarterFilter === "Q2") quarterKey = "Q2 2025";
  else if (quarterFilter === "Q3") quarterKey = "Q3 2025";
  else quarterKey = "Q4 2025";

  const value = quarterly[quarterKey];
  if (value !== undefined && value !== null) {
    return value.toLocaleString("en-US");
  }
  return GRID_EMPTY_AR;
}

function FlowGridCell({ value }) {
  if (isEmptyCellValue(value)) {
    return GRID_EMPTY_AR;
  }
  return <SignedSarTypography value={value} />;
}

/**
 * @param {object} opts
 * @param {string} opts.quarterFilter
 * @param {object} opts.netProfitData
 * @param {(symbol: string, quarter: string) => void | Promise<void>} opts.fetchEvidenceData
 */
export function buildDashboardColumns({ quarterFilter, netProfitData, fetchEvidenceData }) {
  return [
    { field: "symbol", headerName: "رمز الشركة", width: 120, align: "right", headerAlign: "right" },
    { field: "company_name", headerName: "الشركة", width: 200, align: "right", headerAlign: "right" },
    {
      field: "foreign_ownership",
      headerName: "ملكية جميع المستثمرين الأجانب",
      width: 220,
      align: "right",
      headerAlign: "right",
    },
    { field: "max_allowed", headerName: "الملكية الحالية", width: 150, align: "right", headerAlign: "right" },
    {
      field: "investor_limit",
      headerName: "ملكية المستثمر الاستراتيجي الأجنبي",
      width: 220,
      align: "right",
      headerAlign: "right",
    },
    {
      field: "previous_quarter_value",
      headerName: `الأرباح المبقاة للربع السابق (${headerPreviousQuarterLabel(quarterFilter)})`,
      width: 250,
      align: "right",
      headerAlign: "right",
      renderCell: (params) => (
        <RetainedValueWithEvidence
          symbol={params.row.symbol}
          value={params.value}
          quarterFilter={quarterFilter}
          fetchEvidenceData={fetchEvidenceData}
          evidenceKind="previous"
        />
      ),
    },
    {
      field: "current_quarter_value",
      headerName: `الأرباح المبقاة للربع الحالي (${headerCurrentQuarterLabel(quarterFilter)})`,
      width: 250,
      align: "right",
      headerAlign: "right",
      renderCell: (params) => (
        <RetainedValueWithEvidence
          symbol={params.row.symbol}
          value={params.value}
          quarterFilter={quarterFilter}
          fetchEvidenceData={fetchEvidenceData}
          evidenceKind="current"
        />
      ),
    },
    {
      field: "flow",
      headerName: "حجم الزيادة أو النقص في الأرباح المبقاة (التدفق)",
      width: 280,
      align: "right",
      headerAlign: "right",
      renderCell: (params) => <FlowGridCell value={params.value} />,
    },
    {
      field: "foreign_investor_flow",
      headerName: "تدفق الأرباح المبقاة للمستثمر الأجنبي",
      width: 250,
      align: "right",
      headerAlign: "right",
      renderCell: (params) => <FlowGridCell value={params.value} />,
    },
    {
      field: "net_profit",
      headerName: "صافي الربح",
      width: 150,
      align: "right",
      headerAlign: "right",
      renderCell: (params) => (
        <NetProfitGridCell row={params.row} quarterFilter={quarterFilter} netProfitData={netProfitData} />
      ),
    },
    {
      field: "net_profit_foreign_investor",
      headerName: "صافي الربح للمستثمر الأجنبي",
      width: 220,
      align: "right",
      headerAlign: "right",
      renderCell: (params) => <FlowGridCell value={params.value} />,
    },
    {
      field: "distributed_profits_foreign_investor",
      headerName: "الأرباح الموزعة للمستثمر الأجنبي",
      width: 250,
      align: "right",
      headerAlign: "right",
      renderCell: (params) => <FlowGridCell value={params.value} />,
    },
  ];
}
