import PropTypes from "prop-types";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

const WRAPPER_SX = { mt: 2, pb: 0, px: 0 };
const BAR_SX = {
  display: "flex",
  alignItems: "center",
  bgcolor: "#e9f5ee",
  borderRadius: 4,
  px: 2,
  py: 1.2,
  width: "100%",
  boxSizing: "border-box",
  mb: 1.5,
  gap: 1.5,
};
const STRIP_SX = { width: 3, height: 24, bgcolor: "#1e6641", borderRadius: 6, mr: 0 };
const TITLE_SX = {
  fontWeight: 700,
  color: "#1e6641",
  fontSize: 18,
  letterSpacing: 0.1,
  minWidth: 0,
  pr: 1,
};

/** Green section title bar used twice in the sidebar (Sonar duplicate block). */
export function DrawerSectionHeader({ title }) {
  return (
    <Box sx={WRAPPER_SX}>
      <Box sx={BAR_SX}>
        <Box sx={STRIP_SX} />
        <Typography variant="subtitle1" sx={TITLE_SX}>
          {title}
        </Typography>
      </Box>
    </Box>
  );
}

DrawerSectionHeader.propTypes = {
  title: PropTypes.string.isRequired,
};
