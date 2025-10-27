import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';
import { CheckCircle2, XCircle, RotateCw, SkipForward, Download, ArrowLeft } from 'lucide-react';

interface SessionResults {
  session: {
    id: number;
    tester_name: string;
    started_at: string;
    completed_at: string | null;
    status: string;
  };
  checklist: {
    page_type: string;
    items: Array<{
      id: string;
      category: string;
      title?: string; // Legacy field
      description?: string; // Legacy field
      wcag?: string; // Legacy field
      test_item?: string; // New actionable test instruction
      how_to_test?: string; // Step-by-step instructions
      what_to_look_for?: string; // Success criteria
      wcag_reference?: string; // WCAG guideline
      priority: string;
      estimated_time?: number; // Time estimate in minutes
    }>;
  };
  results: Array<{
    item_id: string;
    status: string;
    notes: string | null;
    created_at: string;
  }>;
  progress: {
    passed: number;
    failed: number;
    needs_retest: number;
    skipped: number;
    total: number;
  };
}

export default function SessionResults() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<SessionResults | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [filter, setFilter] = useState<string>('all');

  useEffect(() => {
    loadResults();
  }, [sessionId]);

  const loadResults = async () => {
    try {
      const res = await fetch(`/api/manual-testing/sessions/${sessionId}/results`);
      if (!res.ok) throw new Error('Failed to load results');
      const sessionData = await res.json();
      setData(sessionData);
    } catch (error) {
      console.error('Error loading results:', error);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return <div className="p-8 text-center">Loading results...</div>;
  }

  if (!data) {
    return <div className="p-8 text-center">Results not found</div>;
  }

  const completedCount = data.progress.passed + data.progress.failed + data.progress.needs_retest + data.progress.skipped;
  const progressPercent = (completedCount / data.progress.total) * 100;

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'passed':
        return <CheckCircle2 className="w-5 h-5 text-green-500" />;
      case 'failed':
        return <XCircle className="w-5 h-5 text-destructive" />;
      case 'needs_retest':
        return <RotateCw className="w-5 h-5 text-orange-500" />;
      case 'skipped':
        return <SkipForward className="w-5 h-5 text-muted-foreground" />;
      default:
        return null;
    }
  };

  const getStatusBadge = (status: string) => {
    const classes: Record<string, string> = {
      passed: 'bg-green-600 text-white',
      failed: 'bg-destructive text-destructive-foreground',
      needs_retest: 'bg-orange-500 text-white',
      skipped: 'bg-muted text-muted-foreground'
    };
    return <Badge className={classes[status] || ''}>{status}</Badge>;
  };

  // Build a map of results by item_id for quick lookup
  const resultsMap = new Map(data.results.map(r => [r.item_id, r]));

  // Get all items from checklist with their results (if any)
  const allItemsWithResults = data.checklist.items.map(item => ({
    item,
    result: resultsMap.get(item.id) || null
  }));

  // Filter based on selected filter
  const filteredItems = allItemsWithResults.filter(({ result }) => {
    if (filter === 'all') return true;
    return result && result.status === filter;
  });

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between">
        <Button variant="outline" onClick={() => navigate('/manual-testing/sessions')}>
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Sessions
        </Button>
        <Button variant="outline">
          <Download className="w-4 h-4 mr-2" />
          Export Report
        </Button>
      </div>

      {/* Session Info */}
      <Card>
        <CardHeader>
          <CardTitle>Testing Session Results</CardTitle>
          <CardDescription>
            Tester: {data.session.tester_name} • Page Type: {data.checklist.page_type}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div>
              <div className="text-sm text-muted-foreground">Status</div>
              <div className="font-medium capitalize">{data.session.status}</div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">Started</div>
              <div className="font-medium">
                {new Date(data.session.started_at).toLocaleDateString()}
              </div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">Completed</div>
              <div className="font-medium">
                {data.session.completed_at
                  ? new Date(data.session.completed_at).toLocaleDateString()
                  : 'In progress'}
              </div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">Total Items</div>
              <div className="font-medium">{data.progress.total}</div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">Completion</div>
              <div className="font-medium">{Math.round(progressPercent)}%</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Progress Summary */}
      <Card>
        <CardHeader>
          <CardTitle>Progress Summary</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Progress value={progressPercent} className="h-3" />
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Card className="border-green-200 bg-green-50 dark:border-green-900 dark:bg-green-950">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-2xl font-bold">{data.progress.passed}</div>
                    <div className="text-sm text-muted-foreground">Passed</div>
                  </div>
                  <CheckCircle2 className="w-8 h-8 text-green-600" />
                </div>
              </CardContent>
            </Card>
            <Card className="border-red-200 bg-red-50 dark:border-red-900 dark:bg-red-950">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-2xl font-bold">{data.progress.failed}</div>
                    <div className="text-sm text-muted-foreground">Failed</div>
                  </div>
                  <XCircle className="w-8 h-8 text-destructive" />
                </div>
              </CardContent>
            </Card>
            <Card className="border-orange-200 bg-orange-50 dark:border-orange-900 dark:bg-orange-950">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-2xl font-bold">{data.progress.needs_retest}</div>
                    <div className="text-sm text-muted-foreground">Needs Retest</div>
                  </div>
                  <RotateCw className="w-8 h-8 text-orange-600" />
                </div>
              </CardContent>
            </Card>
            <Card className="border-gray-200 bg-gray-50 dark:border-gray-800 dark:bg-gray-900">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-2xl font-bold">{data.progress.skipped}</div>
                    <div className="text-sm text-muted-foreground">Skipped</div>
                  </div>
                  <SkipForward className="w-8 h-8 text-muted-foreground" />
                </div>
              </CardContent>
            </Card>
          </div>
        </CardContent>
      </Card>

      {/* Filter Buttons */}
      <div className="flex gap-2">
        <Button
          variant={filter === 'all' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setFilter('all')}
        >
          All ({data.results.length})
        </Button>
        <Button
          variant={filter === 'passed' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setFilter('passed')}
        >
          Passed ({data.progress.passed})
        </Button>
        <Button
          variant={filter === 'failed' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setFilter('failed')}
        >
          Failed ({data.progress.failed})
        </Button>
        <Button
          variant={filter === 'needs_retest' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setFilter('needs_retest')}
        >
          Needs Retest ({data.progress.needs_retest})
        </Button>
      </div>

      {/* Detailed Results */}
      <Card>
        <CardHeader>
          <CardTitle>Test Results</CardTitle>
          <CardDescription>Detailed results for each test item</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {filteredItems.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                No results found for this filter
              </div>
            ) : (
              filteredItems.map(({ item, result }) => (
                <div key={item.id} className="border rounded-lg p-4 space-y-3">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        {result ? getStatusIcon(result.status) : <span className="w-5 h-5 rounded-full border-2 border-muted-foreground" />}
                        <Badge variant="outline">{item.category}</Badge>
                        <Badge className="text-xs">{item.priority}</Badge>
                        {item.estimated_time && (
                          <span className="text-xs text-muted-foreground">
                            ⏱️ ~{item.estimated_time} min
                          </span>
                        )}
                      </div>
                      <h4 className="font-medium text-lg mb-2">
                        {item.test_item || item.title}
                      </h4>
                      {item.description && !item.test_item && (
                        <p className="text-sm text-muted-foreground">{item.description}</p>
                      )}
                      {item.how_to_test && (
                        <details className="mt-2 text-sm">
                          <summary className="cursor-pointer text-blue-600 hover:text-blue-800 font-medium">
                            📋 How to Test
                          </summary>
                          <pre className="mt-2 p-3 bg-blue-50 dark:bg-blue-950 rounded border border-blue-200 dark:border-blue-800 text-xs whitespace-pre-wrap font-sans text-blue-900 dark:text-blue-100">
                            {item.how_to_test}
                          </pre>
                        </details>
                      )}
                      {item.what_to_look_for && (
                        <details className="mt-2 text-sm">
                          <summary className="cursor-pointer text-green-600 hover:text-green-800 font-medium">
                            ✓ Success Criteria
                          </summary>
                          <pre className="mt-2 p-3 bg-green-50 dark:bg-green-950 rounded border border-green-200 dark:border-green-800 text-xs whitespace-pre-wrap font-sans text-green-900 dark:text-green-100">
                            {item.what_to_look_for}
                          </pre>
                        </details>
                      )}
                      <div className="text-sm text-muted-foreground mt-2">
                        WCAG: {item.wcag_reference || item.wcag}
                      </div>
                    </div>
                    {result ? getStatusBadge(result.status) : <Badge variant="outline">Not Tested</Badge>}
                  </div>
                  {result?.notes && (
                    <div className="mt-3 pt-3 border-t">
                      <div className="text-sm font-medium mb-1">Tester Notes:</div>
                      <div className="text-sm text-muted-foreground whitespace-pre-wrap">{result.notes}</div>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
