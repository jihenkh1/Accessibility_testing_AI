import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { ThemeShowcase } from '../components/ThemeShowcase'
import { AIStatsSection } from '../components/AIStatsSection'
import { applyTheme, getStoredTheme } from '../utils/themes'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card'
import { Label } from '../components/ui/label'
import { Switch } from '../components/ui/switch'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs'
import { Palette, Sparkles } from 'lucide-react'

export default function Settings() {
  const [searchParams] = useSearchParams()
  const stored = getStoredTheme()
  const [dark, setDark] = useState(stored.isDark)
  const [themeName, setThemeName] = useState(stored.themeName)
  
  // Get initial tab from URL or default to 'appearance'
  const initialTab = searchParams.get('tab') || 'appearance'

  useEffect(() => {
    applyTheme(themeName, dark)
  }, [themeName, dark])

  return (
    <div className="max-w-6xl mx-auto space-y-6 p-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
        <p className="text-muted-foreground">Manage your application preferences and AI features</p>
      </div>

      <Tabs defaultValue={initialTab} className="w-full">
        <TabsList className="grid w-full grid-cols-2 lg:w-[400px]">
          <TabsTrigger value="appearance" className="gap-2">
            <Palette className="h-4 w-4" />
            Appearance
          </TabsTrigger>
          <TabsTrigger value="ai" className="gap-2">
            <Sparkles className="h-4 w-4" />
            AI Features
          </TabsTrigger>
        </TabsList>

        <TabsContent value="appearance" className="mt-6">
          <Card className="border-2">
            <CardHeader>
              <CardTitle>Appearance</CardTitle>
              <CardDescription>Customize how the application looks</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <Label htmlFor="dark-mode">Dark mode</Label>
                  <p className="text-xs text-muted-foreground">Use the dark color scheme</p>
                </div>
                <Switch id="dark-mode" checked={dark} onCheckedChange={setDark} aria-label="Toggle dark mode" />
              </div>

              <div className="pt-2">
                <ThemeShowcase onThemeSelect={setThemeName} />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="ai" className="mt-6">
          <AIStatsSection />
        </TabsContent>
      </Tabs>
    </div>
  )
}
