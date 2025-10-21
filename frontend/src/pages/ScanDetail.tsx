import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { getScan } from '../lib/api'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs'

export default function ScanDetail() {
  const { id } = useParams()
  const scanId = Number(id)
  const { data, isLoading, error } = useQuery({ queryKey: ['scan', scanId], queryFn: () => getScan(scanId), enabled: !Number.isNaN(scanId) })

  if (Number.isNaN(scanId)) return <div className="p-4">Invalid scan id</div>
  return (
    <div className="max-w-5xl mx-auto space-y-4">
      <h1 className="mb-2">Scan #{scanId}</h1>
      {isLoading && <div>Loading�</div>}
      {error && <div className="text-red-600">Failed to load</div>}
      {data && (
        <Tabs defaultValue="summary" className="space-y-3">
          <TabsList>
            <TabsTrigger value="summary">Summary</TabsTrigger>
            <TabsTrigger value="issues">Issues</TabsTrigger>
          </TabsList>
          <TabsContent value="summary">
            <Card className="border-2">
              <CardHeader><CardTitle>Summary</CardTitle></CardHeader>
              <CardContent>
                <pre className="text-xs overflow-auto max-h-96">{JSON.stringify(data, null, 2)}</pre>
              </CardContent>
            </Card>
          </TabsContent>
          <TabsContent value="issues">
            <Card className="border-2">
              <CardHeader><CardTitle>Issues</CardTitle></CardHeader>
              <CardContent>
                <div className="text-sm">
                  View issues table <Link className="text-primary underline" to={`/scan/${scanId}/issues`}>here</Link> for filters and export.
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      )}
    </div>
  )
}
