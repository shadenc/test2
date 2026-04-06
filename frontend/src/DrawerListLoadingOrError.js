import PropTypes from "prop-types";
import ListItem from "@mui/material/ListItem";
import CircularProgress from "@mui/material/CircularProgress";
import Alert from "@mui/material/Alert";

/** Loading spinner or error row for sidebar lists (deduplicates App.js drawer lists). */
export function DrawerListLoadingOrError({ loading, error }) {
  if (loading) {
    return (
      <ListItem sx={{ justifyContent: "center" }}>
        <CircularProgress size={22} sx={{ color: "#1e6641" }} />
      </ListItem>
    );
  }
  if (error) {
    return (
      <ListItem>
        <Alert severity="error">{error}</Alert>
      </ListItem>
    );
  }
  return null;
}

DrawerListLoadingOrError.propTypes = {
  loading: PropTypes.bool.isRequired,
  error: PropTypes.string,
};

DrawerListLoadingOrError.defaultProps = {
  error: null,
};
