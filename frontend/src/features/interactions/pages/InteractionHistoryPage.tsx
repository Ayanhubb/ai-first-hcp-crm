import {
  Box,
  FormControl,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Chip,
} from '@mui/material'
import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAppDispatch, useAppSelector } from '@/app/hooks'
import {
  fetchInteractions,
  setHistoryFilters,
} from '@/features/interactions/historySlice'
import { PageHeader } from '@/shared/components/PageHeader'
import { EmptyState, ErrorState } from '@/shared/components/EmptyState'
import { LoadingState } from '@/shared/components/LoadingState'
import { ROUTES } from '@/shared/constants/routes'
import type { Sentiment } from '@/shared/types'
import { SentimentBadge } from '@/features/ai-assistant/components/SentimentBadge'

export function InteractionHistoryPage() {
  const dispatch = useAppDispatch()
  const navigate = useNavigate()
  const { items, filters, status, error } = useAppSelector((s) => s.history)

  useEffect(() => {
    void dispatch(fetchInteractions(filters))
  }, [dispatch, filters])

  return (
    <Box>
      <PageHeader
        title="Interaction history"
        subtitle="Browse and open past visits"
      />

      <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} sx={{ mb: 2 }}>
        <TextField
          label="HCP name"
          size="small"
          value={filters.hcpName}
          onChange={(e) => dispatch(setHistoryFilters({ hcpName: e.target.value }))}
          fullWidth
        />
        <FormControl size="small" fullWidth>
          <InputLabel id="hist-sentiment">Sentiment</InputLabel>
          <Select
            labelId="hist-sentiment"
            label="Sentiment"
            value={filters.sentiment}
            onChange={(e) =>
              dispatch(
                setHistoryFilters({
                  sentiment: e.target.value as '' | Sentiment,
                }),
              )
            }
          >
            <MenuItem value="">All</MenuItem>
            <MenuItem value="positive">Positive</MenuItem>
            <MenuItem value="neutral">Neutral</MenuItem>
            <MenuItem value="negative">Negative</MenuItem>
          </Select>
        </FormControl>
        <TextField
          label="From"
          type="date"
          size="small"
          value={filters.fromDate}
          onChange={(e) => dispatch(setHistoryFilters({ fromDate: e.target.value }))}
          InputLabelProps={{ shrink: true }}
          fullWidth
        />
        <TextField
          label="To"
          type="date"
          size="small"
          value={filters.toDate}
          onChange={(e) => dispatch(setHistoryFilters({ toDate: e.target.value }))}
          InputLabelProps={{ shrink: true }}
          fullWidth
        />
      </Stack>

      {status === 'loading' && items.length === 0 ? (
        <LoadingState label="Loading history…" />
      ) : null}

      {status === 'failed' ? (
        <ErrorState
          message={error ?? 'Failed to load'}
          onRetry={() => void dispatch(fetchInteractions(filters))}
        />
      ) : null}

      {status === 'succeeded' && items.length === 0 ? (
        <EmptyState
          title="No interactions found"
          description="Adjust filters or log a new interaction from Search HCP."
        />
      ) : null}

      {items.length > 0 ? (
        <TableContainer component={Paper}>
          <Table aria-label="Interaction history">
            <TableHead>
              <TableRow>
                <TableCell>Visit</TableCell>
                <TableCell>HCP</TableCell>
                <TableCell>Channel</TableCell>
                <TableCell>Sentiment</TableCell>
                <TableCell>Summary</TableCell>
                <TableCell>Products</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {items.map((ix) => (
                <TableRow
                  key={ix.id}
                  hover
                  sx={{ cursor: 'pointer' }}
                  onClick={() => navigate(ROUTES.interactionDetail(ix.id))}
                >
                  <TableCell>{new Date(ix.visitAt).toLocaleString()}</TableCell>
                  <TableCell>{ix.hcpName}</TableCell>
                  <TableCell sx={{ textTransform: 'capitalize' }}>
                    {ix.channel.replace('_', ' ')}
                  </TableCell>
                  <TableCell>
                    <SentimentBadge sentiment={ix.sentiment} score={ix.sentimentScore} />
                  </TableCell>
                  <TableCell sx={{ maxWidth: 280 }}>
                    <Box
                      component="span"
                      sx={{
                        display: 'block',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      {ix.summary}
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap>
                      {ix.products.map((p) => (
                        <Chip key={p.id} label={p.name} size="small" variant="outlined" />
                      ))}
                    </Stack>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      ) : null}
    </Box>
  )
}
