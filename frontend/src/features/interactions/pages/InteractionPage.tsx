import { Alert, Box, Collapse, Grid, IconButton, Paper, Stack } from '@mui/material'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'
import ExpandLessIcon from '@mui/icons-material/ExpandLess'
import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useAppDispatch, useAppSelector } from '@/app/hooks'
import { clearAiAssistant } from '@/features/ai-assistant/aiAssistantSlice'
import { AiAssistantPanel } from '@/features/ai-assistant/components/AiAssistantPanel'
import { HcpIdentityHeader } from '@/features/hcp/components/HcpIdentityHeader'
import { setSelectedHcp } from '@/features/hcp/hcpSlice'
import {
  InteractionForm,
  type InteractionFormValues,
} from '@/features/interactions/components/InteractionForm'
import { ReviewSaveBar } from '@/features/interactions/components/ReviewSaveBar'
import { saveInteraction } from '@/features/interactions/historySlice'
import { hcpApi } from '@/services/hcpApi'
import { PageHeader } from '@/shared/components/PageHeader'
import { LoadingState } from '@/shared/components/LoadingState'
import { ROUTES } from '@/shared/constants/routes'
import { showSnackbar } from '@/shared/uiSlice'
import type { Hcp, Sentiment } from '@/shared/types'

function defaultVisitAt() {
  const d = new Date()
  d.setMinutes(d.getMinutes() - d.getTimezoneOffset())
  return d.toISOString().slice(0, 16)
}

export function InteractionPage() {
  const { hcpId = '' } = useParams()
  const dispatch = useAppDispatch()
  const navigate = useNavigate()
  const selectedHcp = useAppSelector((s) => s.hcp.selectedHcp)
  const ai = useAppSelector((s) => s.aiAssistant)
  const saveStatus = useAppSelector((s) => s.history.saveStatus)
  const [panelOpen, setPanelOpen] = useState(true)
  const [hcp, setHcp] = useState<Hcp | null>(
    selectedHcp?.id === hcpId ? selectedHcp : null,
  )
  const [hcpLoading, setHcpLoading] = useState(!hcp)
  const [errors, setErrors] = useState<Partial<Record<keyof InteractionFormValues, string>>>(
    {},
  )

  const [form, setForm] = useState<InteractionFormValues>({
    visitAt: defaultVisitAt(),
    channel: 'in_person',
    notes: '',
    products: [],
    topics: [],
    sentiment: '',
    summary: '',
    followUps: [],
  })

  useEffect(() => {
    let cancelled = false
    if (selectedHcp?.id === hcpId) {
      setHcp(selectedHcp)
      setHcpLoading(false)
      return
    }
    setHcpLoading(true)
    void hcpApi
      .getById(hcpId)
      .then((row) => {
        if (cancelled) return
        setHcp(row)
        dispatch(setSelectedHcp(row))
      })
      .catch(() => {
        if (!cancelled) setHcp(null)
      })
      .finally(() => {
        if (!cancelled) setHcpLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [dispatch, hcpId, selectedHcp])

  useEffect(() => {
    return () => {
      dispatch(clearAiAssistant())
    }
  }, [dispatch])

  if (hcpLoading) {
    return <LoadingState label="Loading HCP…" />
  }

  if (!hcp) {
    return <Alert severity="error">HCP not found.</Alert>
  }

  const patchForm = (patch: Partial<InteractionFormValues>) => {
    setForm((prev) => ({ ...prev, ...patch }))
  }

  const acceptAiToForm = (result?: {
    summary: string
    sentiment: Sentiment | null
    products: InteractionFormValues['products']
    topics: string[]
    followUps: InteractionFormValues['followUps']
  }) => {
    const src = result ?? {
      summary: ai.summary,
      sentiment: ai.sentiment,
      products: ai.products,
      topics: ai.topics,
      followUps: ai.followUps,
    }
    patchForm({
      summary: src.summary || form.summary,
      sentiment: (src.sentiment as Sentiment) || form.sentiment,
      products: src.products.length ? src.products : form.products,
      topics: src.topics.length ? src.topics : form.topics,
      followUps: src.followUps.length ? src.followUps : form.followUps,
    })
  }
  const validate = () => {
    const next: Partial<Record<keyof InteractionFormValues, string>> = {}
    if (!form.notes.trim()) next.notes = 'Notes are required'
    if (!form.visitAt) next.visitAt = 'Visit date is required'
    if (!form.channel) next.channel = 'Channel is required'
    setErrors(next)
    return Object.keys(next).length === 0
  }

  const handleSave = async () => {
    if (!validate()) {
      dispatch(
        showSnackbar({ message: 'Fix required fields before saving.', severity: 'warning' }),
      )
      return
    }

    const result = await dispatch(
      saveInteraction({
        hcpId: hcp.id,
        visitAt: new Date(form.visitAt).toISOString(),
        channel: form.channel,
        notes: form.notes,
        summary: form.summary || form.notes.slice(0, 160),
        sentiment: (form.sentiment || ai.sentiment || 'neutral') as Sentiment,
        sentimentScore: ai.sentimentScore ?? 0.5,
        productIds: form.products.map((p) => p.id),
        topics: form.topics,
        followUps: form.followUps.map((f) => ({ text: f.text, dueDate: f.dueDate })),
        aiRunId: ai.aiRunId,
      }),
    )

    if (saveInteraction.fulfilled.match(result)) {
      dispatch(showSnackbar({ message: 'Interaction saved.', severity: 'success' }))
      navigate(ROUTES.interactionDetail(result.payload.id))
    } else {
      dispatch(
        showSnackbar({
          message: (result.payload as string) || 'Save failed',
          severity: 'error',
        }),
      )
    }
  }

  return (
    <Box>
      <PageHeader
        title="Log interaction"
        subtitle="Capture visit notes and review AI suggestions before saving"
      />
      <HcpIdentityHeader hcp={hcp} />

      <Grid container spacing={2}>
        <Grid item xs={12} md={7}>
          <Paper sx={{ p: 2.5 }}>
            <InteractionForm values={form} errors={errors} onChange={patchForm} />
          </Paper>
          <ReviewSaveBar
            onSave={() => void handleSave()}
            saving={saveStatus === 'loading'}
          />
        </Grid>
        <Grid item xs={12} md={5}>
          <Paper sx={{ p: 2.5 }}>
            <Stack direction="row" justifyContent="flex-end" sx={{ mb: 1, display: { md: 'none' } }}>
              <IconButton
                aria-label={panelOpen ? 'Collapse AI panel' : 'Expand AI panel'}
                onClick={() => setPanelOpen((o) => !o)}
                size="small"
              >
                {panelOpen ? <ExpandLessIcon /> : <ExpandMoreIcon />}
              </IconButton>
            </Stack>
            <Collapse in={panelOpen} sx={{ display: { xs: 'block', md: 'block' } }}>
              <AiAssistantPanel
                notes={form.notes}
                hcpId={hcp.id}
                onAcceptToForm={acceptAiToForm}
              />
            </Collapse>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  )
}
