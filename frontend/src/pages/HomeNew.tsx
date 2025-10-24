import { useNavigate } from 'react-router-dom'
import { HomePage } from './HomePage'

export default function HomeNew() {
  const navigate = useNavigate()
  const go = (page: string) => {
    const map: Record<string,string> = {
      home: '/home',
      upload: '/upload',
      dashboard: '/dashboard',
      runs: '/dashboard',
      'scan-detail': '/dashboard',
      pipeline: '/pipeline',
      settings: '/settings',
    }
    navigate(map[page] || '/home')
  }
  return <HomePage onNavigate={go} />
}
