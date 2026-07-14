import {
  Box,
  Drawer,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Typography,
  useMediaQuery,
} from '@mui/material'
import { useTheme } from '@mui/material/styles'
import DashboardOutlinedIcon from '@mui/icons-material/DashboardOutlined'
import SearchOutlinedIcon from '@mui/icons-material/SearchOutlined'
import HistoryOutlinedIcon from '@mui/icons-material/HistoryOutlined'
import { NavLink, useLocation } from 'react-router-dom'
import { useAppDispatch, useAppSelector } from '@/app/hooks'
import { setSideNavOpen } from '@/shared/uiSlice'
import { ROUTES } from '@/shared/constants/routes'

const DRAWER_WIDTH = 240

const navItems = [
  { label: 'Dashboard', to: ROUTES.dashboard, icon: <DashboardOutlinedIcon /> },
  { label: 'Search HCP', to: ROUTES.hcps, icon: <SearchOutlinedIcon /> },
  { label: 'History', to: ROUTES.interactions, icon: <HistoryOutlinedIcon /> },
]

export function SideNav() {
  const theme = useTheme()
  const isDesktop = useMediaQuery(theme.breakpoints.up('md'))
  const open = useAppSelector((s) => s.ui.sideNavOpen)
  const dispatch = useAppDispatch()
  const location = useLocation()

  const content = (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <Toolbar sx={{ px: 2 }}>
        <Typography variant="subtitle2" color="text.secondary">
          Navigation
        </Typography>
      </Toolbar>
      <List sx={{ px: 1 }}>
        {navItems.map((item) => {
          const selected =
            item.to === ROUTES.dashboard
              ? location.pathname === ROUTES.dashboard
              : location.pathname.startsWith(item.to)
          return (
            <ListItemButton
              key={item.to}
              component={NavLink}
              to={item.to}
              selected={selected}
              onClick={() => {
                if (!isDesktop) dispatch(setSideNavOpen(false))
              }}
              sx={{ borderRadius: 1.5, mb: 0.5 }}
            >
              <ListItemIcon sx={{ minWidth: 40 }}>{item.icon}</ListItemIcon>
              <ListItemText primary={item.label} />
            </ListItemButton>
          )
        })}
      </List>
    </Box>
  )

  if (isDesktop) {
    return (
      <Drawer
        variant="persistent"
        open={open}
        sx={{
          width: open ? DRAWER_WIDTH : 0,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: DRAWER_WIDTH,
            boxSizing: 'border-box',
            top: 64,
            height: 'calc(100% - 64px)',
          },
        }}
      >
        {content}
      </Drawer>
    )
  }

  return (
    <Drawer
      variant="temporary"
      open={open}
      onClose={() => dispatch(setSideNavOpen(false))}
      ModalProps={{ keepMounted: true }}
      sx={{
        '& .MuiDrawer-paper': { width: DRAWER_WIDTH, boxSizing: 'border-box' },
      }}
    >
      {content}
    </Drawer>
  )
}

export const sideNavWidth = DRAWER_WIDTH
