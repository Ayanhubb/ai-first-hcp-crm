import { Box, Button, LinearProgress, Stack } from '@mui/material'
import PersonAddAlt1OutlinedIcon from '@mui/icons-material/PersonAddAlt1Outlined'
import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAppDispatch, useAppSelector } from '@/app/hooks'
import { searchHcps, setFilters, setQuery, setSelectedHcp } from '@/features/hcp/hcpSlice'
import { clearAiAssistant } from '@/features/ai-assistant/aiAssistantSlice'
import { AddHcpDialog } from '@/features/hcp/components/AddHcpDialog'
import { SearchBar } from '@/features/hcp/components/SearchBar'
import { FilterRow } from '@/features/hcp/components/FilterRow'
import { HcpResultsTable } from '@/features/hcp/components/HcpResultsTable'
import { PageHeader } from '@/shared/components/PageHeader'
import { ROUTES } from '@/shared/constants/routes'
import { showSnackbar } from '@/shared/uiSlice'
import { useDebouncedValue } from '@/shared/hooks/useDebouncedValue'
import type { Hcp } from '@/shared/types'

export function HcpSearchPage() {
  const dispatch = useAppDispatch()
  const navigate = useNavigate()
  const { query, filters, results, status } = useAppSelector((s) => s.hcp)
  const debouncedQuery = useDebouncedValue(query, 350)
  const [addOpen, setAddOpen] = useState(false)

  const specialties = useMemo(
    () =>
      [...new Set(results.map((h) => h.specialty).filter(Boolean))].sort((a, b) =>
        a.localeCompare(b),
      ),
    [results],
  )
  const cities = useMemo(
    () =>
      [...new Set(results.map((h) => h.city).filter(Boolean))].sort((a, b) =>
        a.localeCompare(b),
      ),
    [results],
  )

  useEffect(() => {
    void dispatch(
      searchHcps({
        query: debouncedQuery,
        specialty: filters.specialty,
        city: filters.city,
      }),
    )
  }, [dispatch, debouncedQuery, filters.specialty, filters.city])

  const handleLog = (hcp: Hcp) => {
    dispatch(setSelectedHcp(hcp))
    dispatch(clearAiAssistant())
    navigate(ROUTES.newInteraction(hcp.id))
  }

  const handleCreated = (hcp: Hcp) => {
    dispatch(setQuery(hcp.name))
    dispatch(showSnackbar({ message: `${hcp.name} added.`, severity: 'success' }))
    void dispatch(
      searchHcps({
        query: hcp.name,
        specialty: filters.specialty,
        city: filters.city,
      }),
    )
  }

  return (
    <Box>
      <PageHeader
        title="Search HCP"
        subtitle="Find a healthcare professional to log an interaction"
        actions={
          <Button
            type="button"
            variant="contained"
            startIcon={<PersonAddAlt1OutlinedIcon />}
            onClick={() => setAddOpen(true)}
          >
            Add HCP
          </Button>
        }
      />
      <Stack spacing={2} sx={{ mb: 2 }}>
        <SearchBar value={query} onChange={(v) => dispatch(setQuery(v))} />
        <FilterRow
          specialty={filters.specialty}
          city={filters.city}
          specialties={specialties}
          cities={cities}
          onSpecialtyChange={(v) => dispatch(setFilters({ specialty: v }))}
          onCityChange={(v) => dispatch(setFilters({ city: v }))}
        />
        {status === 'loading' ? <LinearProgress aria-label="Searching" /> : null}
      </Stack>
      <HcpResultsTable
        rows={results}
        loading={status === 'loading'}
        onLogInteraction={handleLog}
      />
      <AddHcpDialog
        open={addOpen}
        onClose={() => setAddOpen(false)}
        onCreated={handleCreated}
      />
    </Box>
  )
}
