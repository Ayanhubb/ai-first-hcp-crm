import {
  Button,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material'
import type { Hcp } from '@/shared/types'

type HcpResultsTableProps = {
  rows: Hcp[]
  loading?: boolean
  onLogInteraction: (hcp: Hcp) => void
}

export function HcpResultsTable({
  rows,
  loading,
  onLogInteraction,
}: HcpResultsTableProps) {
  if (!loading && rows.length === 0) {
    return (
      <Typography color="text.secondary" sx={{ py: 3 }}>
        No HCPs match your search.
      </Typography>
    )
  }

  return (
    <TableContainer component={Paper}>
      <Table size="medium" aria-label="HCP search results">
        <TableHead>
          <TableRow>
            <TableCell>Name</TableCell>
            <TableCell>Specialty</TableCell>
            <TableCell>Institution</TableCell>
            <TableCell>City</TableCell>
            <TableCell align="right">Action</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {rows.map((hcp) => (
            <TableRow key={hcp.id} hover>
              <TableCell>{hcp.name}</TableCell>
              <TableCell>{hcp.specialty}</TableCell>
              <TableCell>{hcp.institution}</TableCell>
              <TableCell>{hcp.city}</TableCell>
              <TableCell align="right">
                <Button
                  size="small"
                  variant="outlined"
                  onClick={() => onLogInteraction(hcp)}
                >
                  Log Interaction
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  )
}
