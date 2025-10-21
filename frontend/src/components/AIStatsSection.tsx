import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getAIUsageStats, resetAIUsageStats, getAICacheStats, cleanupAICache } from '../lib/api'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Badge } from '../components/ui/badge'
import { Skeleton } from '../components/ui/skeleton'
import { 
  Sparkles, 
  Database, 
  TrendingUp, 
  DollarSign, 
  CheckCircle, 
  XCircle, 
  RefreshCw, 
  Trash2,
  Clock,
  BarChart3
} from 'lucide-react'
import { Alert, AlertDescription } from '../components/ui/alert'

export function AIStatsSection() {
  const queryClient = useQueryClient()
  
  // Query for usage stats
  const { data: usageData, isLoading: usageLoading, refetch: refetchUsage } = useQuery({
    queryKey: ['ai-usage-stats'],
    queryFn: getAIUsageStats,
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  // Query for cache stats
  const { data: cacheData, isLoading: cacheLoading, refetch: refetchCache } = useQuery({
    queryKey: ['ai-cache-stats'],
    queryFn: getAICacheStats,
    refetchInterval: 60000, // Refresh every minute
  })

  // Mutation for resetting usage stats
  const resetMutation = useMutation({
    mutationFn: resetAIUsageStats,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ai-usage-stats'] })
    },
  })

  // Mutation for cleaning up cache
  const cleanupMutation = useMutation({
    mutationFn: cleanupAICache,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ai-cache-stats'] })
    },
  })

  const usage = usageData?.stats
  const cache = cacheData?.stats

  return (
    <div className="space-y-6">
      {/* Usage Statistics Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-purple-500" />
                AI Usage Statistics
              </CardTitle>
              <CardDescription>
                Token usage, costs, and success rates
              </CardDescription>
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => refetchUsage()}
                disabled={usageLoading}
              >
                <RefreshCw className="h-4 w-4 mr-1" />
                Refresh
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => resetMutation.mutate()}
                disabled={resetMutation.isPending || !usageData?.available}
              >
                <Trash2 className="h-4 w-4 mr-1" />
                Reset
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {usageLoading ? (
            <div className="space-y-3">
              <Skeleton className="h-16 w-full" />
              <Skeleton className="h-16 w-full" />
            </div>
          ) : !usageData?.available ? (
            <Alert>
              <AlertDescription>
                AI usage statistics not available. {usageData?.error || 'AI client may not be initialized.'}
              </AlertDescription>
            </Alert>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              {/* Total Requests */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Total Requests</span>
                  <BarChart3 className="h-4 w-4 text-muted-foreground" />
                </div>
                <div className="text-2xl font-bold">{usage?.total_requests.toLocaleString() || 0}</div>
                <div className="flex gap-2 text-xs">
                  <Badge variant="outline" className="gap-1">
                    <CheckCircle className="h-3 w-3 text-green-500" />
                    {usage?.successful_requests || 0} success
                  </Badge>
                  <Badge variant="outline" className="gap-1">
                    <XCircle className="h-3 w-3 text-red-500" />
                    {usage?.failed_requests || 0} failed
                  </Badge>
                </div>
              </div>

              {/* Token Usage */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Total Tokens</span>
                  <TrendingUp className="h-4 w-4 text-muted-foreground" />
                </div>
                <div className="text-2xl font-bold">{usage?.total_tokens.toLocaleString() || 0}</div>
                <div className="text-xs text-muted-foreground">
                  {usage?.total_prompt_tokens.toLocaleString() || 0} prompt + {usage?.total_completion_tokens.toLocaleString() || 0} completion
                </div>
              </div>

              {/* Cost */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Estimated Cost</span>
                  <DollarSign className="h-4 w-4 text-muted-foreground" />
                </div>
                <div className="text-2xl font-bold">
                  ${usage?.estimated_cost_usd.toFixed(4) || '0.0000'}
                </div>
                <div className="text-xs text-muted-foreground">
                  {usage?.estimated_cost_usd === 0 ? 'Free model' : 'Based on token usage'}
                </div>
              </div>

              {/* Success Rate */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Success Rate</span>
                  <CheckCircle className="h-4 w-4 text-muted-foreground" />
                </div>
                <div className="text-2xl font-bold">{usage?.success_rate.toFixed(1) || 0}%</div>
                <div className="text-xs text-muted-foreground">
                  {usage && usage.success_rate >= 95 ? (
                    <span className="text-green-600">Excellent</span>
                  ) : usage && usage.success_rate >= 80 ? (
                    <span className="text-yellow-600">Good</span>
                  ) : (
                    <span className="text-red-600">Needs attention</span>
                  )}
                </div>
              </div>
            </div>
          )}

          {resetMutation.isSuccess && (
            <Alert className="mt-4">
              <CheckCircle className="h-4 w-4" />
              <AlertDescription>Usage statistics reset successfully</AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Cache Statistics Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Database className="h-5 w-5 text-blue-500" />
                AI Cache Statistics
              </CardTitle>
              <CardDescription>
                Cache entries, expiration, and disk usage
              </CardDescription>
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => refetchCache()}
                disabled={cacheLoading}
              >
                <RefreshCw className="h-4 w-4 mr-1" />
                Refresh
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => cleanupMutation.mutate()}
                disabled={cleanupMutation.isPending || !cacheData?.available}
              >
                <Trash2 className="h-4 w-4 mr-1" />
                Cleanup Expired
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {cacheLoading ? (
            <div className="space-y-3">
              <Skeleton className="h-16 w-full" />
              <Skeleton className="h-16 w-full" />
            </div>
          ) : !cacheData?.available ? (
            <Alert>
              <AlertDescription>
                AI cache statistics not available. {cacheData?.error || 'Cache may not be enabled.'}
              </AlertDescription>
            </Alert>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              {/* Total Entries */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Total Entries</span>
                  <Database className="h-4 w-4 text-muted-foreground" />
                </div>
                <div className="text-2xl font-bold">{cache?.total_entries.toLocaleString() || 0}</div>
                <div className="text-xs text-muted-foreground">
                  Cached AI responses
                </div>
              </div>

              {/* Valid Entries */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Valid Entries</span>
                  <CheckCircle className="h-4 w-4 text-muted-foreground" />
                </div>
                <div className="text-2xl font-bold text-green-600">
                  {cache?.valid_entries.toLocaleString() || 0}
                </div>
                <div className="text-xs text-muted-foreground">
                  Not expired yet
                </div>
              </div>

              {/* Expired Entries */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Expired Entries</span>
                  <XCircle className="h-4 w-4 text-muted-foreground" />
                </div>
                <div className="text-2xl font-bold text-orange-600">
                  {cache?.expired_entries.toLocaleString() || 0}
                </div>
                <div className="text-xs text-muted-foreground">
                  Ready for cleanup
                </div>
              </div>

              {/* TTL */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Cache TTL</span>
                  <Clock className="h-4 w-4 text-muted-foreground" />
                </div>
                <div className="text-2xl font-bold">{cache?.ttl_days || 0} days</div>
                <div className="text-xs text-muted-foreground">
                  Time to live
                </div>
              </div>
            </div>
          )}

          {cache && (cache.oldest_entry || cache.newest_entry) && (
            <div className="mt-4 grid gap-2 text-sm">
              {cache.oldest_entry && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Oldest entry:</span>
                  <span>{new Date(cache.oldest_entry).toLocaleString()}</span>
                </div>
              )}
              {cache.newest_entry && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Newest entry:</span>
                  <span>{new Date(cache.newest_entry).toLocaleString()}</span>
                </div>
              )}
            </div>
          )}

          {cleanupMutation.isSuccess && cleanupMutation.data?.success && (
            <Alert className="mt-4">
              <CheckCircle className="h-4 w-4" />
              <AlertDescription>
                {cleanupMutation.data.message || `Removed ${cleanupMutation.data.deleted} expired entries`}
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
