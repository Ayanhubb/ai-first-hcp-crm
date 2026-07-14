import { useRef, useState } from 'react'
import {
  Alert,
  Box,
  Button,
  Skeleton,
  Stack,
  Typography,
} from '@mui/material'
import AutoAwesomeOutlinedIcon from '@mui/icons-material/AutoAwesomeOutlined'
import { useAppDispatch, useAppSelector } from '@/app/hooks'
import { runAssist, runEditAssist } from '@/features/ai-assistant/aiAssistantSlice'
import { HistorySummary } from '@/features/ai-assistant/components/HistorySummary'
import { SummaryCard } from '@/features/ai-assistant/components/SummaryCard'
import { SentimentBadge } from '@/features/ai-assistant/components/SentimentBadge'
import { ProductsList } from '@/features/ai-assistant/components/ProductsList'
import { TopicsList } from '@/features/ai-assistant/components/TopicsList'
import { FollowUpSuggestions } from '@/features/ai-assistant/components/FollowUpSuggestions'
import { EditAssistControls } from '@/features/ai-assistant/components/EditAssistControls'
import { getAccessToken } from '@/services/http'
import { showSnackbar } from '@/shared/uiSlice'
import type { AiAssistantResult } from '@/shared/types'

type AiAssistantPanelProps = {
  notes: string
  hcpId: string
  onAcceptToForm: (result?: AiAssistantResult & { aiRunId?: string }) => void
}

export function AiAssistantPanel({
  notes,
  hcpId,
  onAcceptToForm,
}: AiAssistantPanelProps) {
  const dispatch = useAppDispatch()
  const ai = useAppSelector((s) => s.aiAssistant)
  const reduxLoading = ai.runStatus === 'loading'
  const [localBusy, setLocalBusy] = useState(false)
  const [statusMsg, setStatusMsg] = useState<string | null>(null)
  const notesRef = useRef(notes)
  notesRef.current = notes
  const hcpIdRef = useRef(hcpId)
  hcpIdRef.current = hcpId

  const loading = reduxLoading || localBusy
  const hasResult = ai.runStatus === 'succeeded'

  const handleAnalyze = async () => {
    const currentNotes = (notesRef.current || '').trim()
    const currentHcpId = hcpIdRef.current

    if (currentNotes.length < 20) {
      const msg = 'Enter at least 20 characters of notes before Analyze.'
      setStatusMsg(msg)
      dispatch(showSnackbar({ message: msg, severity: 'warning' }))
      return
    }
    if (!currentHcpId) {
      const msg = 'HCP is missing — go back and select a doctor again.'
      setStatusMsg(msg)
      dispatch(showSnackbar({ message: msg, severity: 'error' }))
      return
    }
    if (!getAccessToken()) {
      const msg = 'Session expired — please log out and log in again.'
      setStatusMsg(msg)
      dispatch(showSnackbar({ message: msg, severity: 'error' }))
      return
    }

    setLocalBusy(true)
    setStatusMsg('Calling AI… this can take a few seconds.')
    try {
      const result = await dispatch(
        runAssist({ notes: currentNotes, hcpId: currentHcpId }),
      )
      if (runAssist.fulfilled.match(result)) {
        const payload = result.payload
        onAcceptToForm(payload)
        if (payload.errors?.length && !payload.summary) {
          const msg = payload.errors[0] || 'AI returned no suggestions.'
          setStatusMsg(msg)
          dispatch(showSnackbar({ message: msg, severity: 'warning' }))
        } else {
          const msg = 'AI filled suggestions — review the form, then Save.'
          setStatusMsg(msg)
          dispatch(showSnackbar({ message: msg, severity: 'success' }))
        }
      } else {
        const msg =
          (typeof result.payload === 'string' && result.payload) ||
          'AI request failed. Try again or re-login.'
        setStatusMsg(msg)
        dispatch(showSnackbar({ message: msg, severity: 'warning' }))
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Unexpected AI error'
      setStatusMsg(msg)
      dispatch(showSnackbar({ message: msg, severity: 'error' }))
    } finally {
      setLocalBusy(false)
    }
  }

  const handleEdit = (instruction: string) => {
    void dispatch(
      runEditAssist({
        instruction,
        currentSummary: ai.summary,
        hcpId: hcpIdRef.current,
        notes: notesRef.current,
      }),
    )
  }

  return (
    <Box
      component="aside"
      aria-label="AI Assistant"
      sx={{
        display: 'flex',
        flexDirection: 'column',
        gap: 1.5,
        height: '100%',
      }}
    >
      <Stack direction="row" justifyContent="space-between" alignItems="center">
        <Stack direction="row" spacing={1} alignItems="center">
          <AutoAwesomeOutlinedIcon color="primary" fontSize="small" />
          <Typography variant="h6">AI Assistant</Typography>
        </Stack>
        <SentimentBadge sentiment={ai.sentiment} score={ai.sentimentScore} />
      </Stack>

      <Typography variant="body2" color="text.secondary">
        Write notes → Analyze → AI fills summary/products/topics/follow-ups.
      </Typography>

      <Stack direction="row" spacing={1}>
        <Button
          type="button"
          variant="contained"
          onClick={() => void handleAnalyze()}
          disabled={loading}
          startIcon={<AutoAwesomeOutlinedIcon />}
        >
          {loading ? 'Analyzing…' : 'Analyze'}
        </Button>
        <Button
          type="button"
          variant="outlined"
          onClick={() => onAcceptToForm()}
          disabled={!hasResult || loading}
        >
          Apply to form
        </Button>
      </Stack>

      {statusMsg ? (
        <Alert severity={loading ? 'info' : hasResult ? 'success' : 'warning'}>
          {statusMsg}
        </Alert>
      ) : null}

      {ai.errors.length > 0 ? (
        <Alert severity="warning">{ai.errors.join(' · ')}</Alert>
      ) : null}

      {loading ? (
        <Stack spacing={1.5}>
          <Skeleton variant="rounded" height={72} />
          <Skeleton variant="rounded" height={72} />
          <Skeleton variant="rounded" height={56} />
          <Skeleton variant="rounded" height={56} />
        </Stack>
      ) : (
        <Stack spacing={1.5}>
          <HistorySummary text={ai.historySummary} />
          <SummaryCard title="Summary" body={ai.summary} />
          <ProductsList products={ai.products} />
          <TopicsList topics={ai.topics} />
          <FollowUpSuggestions followUps={ai.followUps} />
          <EditAssistControls
            disabled={!hasResult}
            loading={loading}
            onApply={handleEdit}
          />
        </Stack>
      )}
    </Box>
  )
}
