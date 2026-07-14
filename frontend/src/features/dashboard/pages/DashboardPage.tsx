import {
  Box,
  Button,
  Card,
  CardActionArea,
  CardContent,
  Grid,
  List,
  ListItem,
  ListItemText,
  Paper,
  Skeleton,
  Typography,
} from '@mui/material'
import SearchOutlinedIcon from '@mui/icons-material/SearchOutlined'
import { useEffect } from 'react'
import { Link as RouterLink } from 'react-router-dom'
import { useAppDispatch, useAppSelector } from '@/app/hooks'
import { fetchDashboardSummary } from '@/features/dashboard/dashboardSlice'
import { PageHeader } from '@/shared/components/PageHeader'
import { EmptyState, ErrorState } from '@/shared/components/EmptyState'
import { ROUTES } from '@/shared/constants/routes'

export function DashboardPage() {
  const dispatch = useAppDispatch()
  const { summary, status, error } = useAppSelector((s) => s.dashboard)

  useEffect(() => {
    void dispatch(fetchDashboardSummary())
  }, [dispatch])

  if (status === 'failed') {
    return (
      <ErrorState
        message={error ?? 'Unable to load dashboard'}
        onRetry={() => void dispatch(fetchDashboardSummary())}
      />
    )
  }

  const loading = status === 'loading' || status === 'idle'

  return (
    <Box>
      <PageHeader
        title="Dashboard"
        subtitle="Your weekly activity and open follow-ups"
        actions={
          <Button
            component={RouterLink}
            to={ROUTES.hcps}
            variant="contained"
            startIcon={<SearchOutlinedIcon />}
          >
            Search HCP
          </Button>
        }
      />

      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6}>
          <Paper sx={{ p: 2.5 }}>
            {loading ? (
              <Skeleton height={64} />
            ) : (
              <>
                <Typography color="text.secondary" variant="body2">
                  Interactions this week
                </Typography>
                <Typography variant="h3" sx={{ mt: 0.5 }}>
                  {summary?.interactionsThisWeek ?? 0}
                </Typography>
              </>
            )}
          </Paper>
        </Grid>
        <Grid item xs={12} sm={6}>
          <Paper sx={{ p: 2.5 }}>
            {loading ? (
              <Skeleton height={64} />
            ) : (
              <>
                <Typography color="text.secondary" variant="body2">
                  Open follow-ups
                </Typography>
                <Typography variant="h3" sx={{ mt: 0.5 }}>
                  {summary?.openFollowUps ?? 0}
                </Typography>
              </>
            )}
          </Paper>
        </Grid>
      </Grid>

      <Grid container spacing={2}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" sx={{ mb: 1 }}>
              Recent interactions
            </Typography>
            {loading ? (
              <Skeleton variant="rounded" height={180} />
            ) : summary?.recentInteractions.length ? (
              <List disablePadding>
                {summary.recentInteractions.map((ix) => (
                  <ListItem
                    key={ix.id}
                    component={RouterLink}
                    to={ROUTES.interactionDetail(ix.id)}
                    sx={{
                      textDecoration: 'none',
                      color: 'inherit',
                      borderRadius: 1,
                      '&:hover': { bgcolor: 'action.hover' },
                    }}
                  >
                    <ListItemText
                      primary={ix.hcpName}
                      secondary={`${new Date(ix.visitAt).toLocaleString()} · ${ix.summary}`}
                      secondaryTypographyProps={{ noWrap: true }}
                    />
                  </ListItem>
                ))}
              </List>
            ) : (
              <EmptyState
                title="No interactions yet"
                description="Search for an HCP and log your first visit."
              />
            )}
          </Paper>
        </Grid>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" sx={{ mb: 1 }}>
              Pending follow-ups
            </Typography>
            {loading ? (
              <Skeleton variant="rounded" height={180} />
            ) : summary?.pendingFollowUps.length ? (
              <Grid container spacing={1.5}>
                {summary.pendingFollowUps.map((fu) => (
                  <Grid item xs={12} key={fu.id}>
                    <Card variant="outlined">
                      <CardActionArea
                        component={RouterLink}
                        to={ROUTES.interactionDetail(fu.interactionId)}
                      >
                        <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
                          <Typography variant="subtitle2">{fu.text}</Typography>
                          <Typography variant="body2" color="text.secondary">
                            {fu.hcpName}
                            {fu.dueDate ? ` · due ${fu.dueDate}` : ''}
                          </Typography>
                        </CardContent>
                      </CardActionArea>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            ) : (
              <EmptyState title="No open follow-ups" />
            )}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  )
}
