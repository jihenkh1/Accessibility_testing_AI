import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { 
  Monitor, 
  Keyboard, 
  ZoomIn, 
  AlertTriangle, 
  FileText, 
  Plus,
  Calendar,
  Bug,
  CheckCircle2,
  FolderKanban,
  ChevronDown,
  ChevronRight,
  ExternalLink,
  Filter,
  X,
  AlertCircle,
  HelpCircle,
  Info,
  Bot,
} from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';
import { BugReportDialog } from '../components/BugReportDialog';

const api = {
  fetchChecklist: (tool: string) => 
    axios.get(`/api/manual-testing-v2/checklists/${tool}`).then(res => res.data),
  fetchTestingMethodStats: () => 
    axios.get('/api/manual-testing-v2/testing-methods/stats').then(res => res.data),
  fetchBugs: (filters?: any) => {
    const params = new URLSearchParams(filters).toString();
    return axios.get(`/api/manual-testing-v2/bugs?${params}`).then(res => res.data);
  },
  fetchAutomatedContext: (projectName?: string) => {
    const params = projectName ? `?project_name=${encodeURIComponent(projectName)}` : '';
    return axios.get(`/api/manual-testing-v2/automated-context${params}`).then(res => res.data);
  },
  fetchProjects: () => 
    axios.get('/api/projects').then(res => res.data),
};

interface TestingMethodCardProps {
  tool: string;
  name: string;
  description: string;
  icon: React.ReactNode;
  stats?: {
    bug_count: number;
    last_tested: string | null;
  };
  onStart: () => void;
}

function TestingMethodCard({ tool, name, description, icon, stats, onStart }: TestingMethodCardProps) {
  return (
    <Card className="hover:shadow-lg transition-shadow h-full flex flex-col">
      <CardHeader className="pb-3 min-h-[110px]">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary/10 rounded-lg">
              {icon}
            </div>
            <div>
              <CardTitle className="text-lg">{name}</CardTitle>
              <CardDescription className="text-sm mt-1 line-clamp-2 min-h-[38px]">{description}</CardDescription>
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col justify-between gap-4">
        <div className="flex items-center justify-between text-sm text-muted-foreground min-h-[48px] flex-wrap gap-2">
          <div className="flex items-center gap-1">
            <Bug className="w-4 h-4" />
            <span>{stats?.bug_count ?? 0} {(stats?.bug_count ?? 0) === 1 ? 'bug' : 'bugs'}</span>
          </div>
          {stats?.last_tested ? (
            <div className="flex items-center gap-1">
              <Calendar className="w-4 h-4" />
              <span>Last tested: {new Date(stats.last_tested).toLocaleDateString()}</span>
            </div>
          ) : null}
        </div>
        <Button onClick={onStart} className="w-full mt-auto">
          <FileText className="w-4 h-4 mr-2" />
          Start Testing
        </Button>
      </CardContent>
    </Card>
  );
}

interface BugItemProps {
  bug: any;
  onClick: () => void;
}

function BugItem({ bug, onClick }: BugItemProps) {
  const severityColors: Record<string, 'destructive' | 'default' | 'secondary'> = {
    Critical: 'destructive',
    High: 'destructive',
    Medium: 'default',
    Low: 'secondary'
  };

  return (
    <div 
      onClick={onClick}
      className="p-4 border rounded-lg hover:bg-accent cursor-pointer transition-colors"
    >
      <div className="flex items-start justify-between mb-2">
        <h4 className="font-medium text-sm line-clamp-1">{bug.title}</h4>
        <Badge variant={severityColors[bug.severity] || 'default'} className="text-xs">
          {bug.severity}
        </Badge>
      </div>
      <div className="flex items-center gap-2 text-xs text-muted-foreground mb-2">
        <Badge variant="outline" className="text-xs">{bug.wcag_criterion}</Badge>
        <span>•</span>
        <span>{bug.testing_tool}</span>
      </div>
      <p className="text-xs text-muted-foreground line-clamp-2">{bug.description}</p>
    </div>
  );
}

export default function ManualTestingDashboard() {
  const navigate = useNavigate();
  const [selectedTool, setSelectedTool] = useState<string | null>(null);
  const [selectedBug, setSelectedBug] = useState<any>(null);
  const [bugReportOpen, setBugReportOpen] = useState(false);
  const [bugPrefillData, setBugPrefillData] = useState<any>({});
  const [selectedProject, setSelectedProject] = useState<string>('all');
  const [expandedItems, setExpandedItems] = useState<Set<number>>(new Set());
  const [levelFilter, setLevelFilter] = useState<string>('all');
  const [failedItems, setFailedItems] = useState<Map<number, { description: string; showInput: boolean }>>(new Map());
  const [showKeyboardHelp, setShowKeyboardHelp] = useState(false);
  const [focusedItemIndex, setFocusedItemIndex] = useState<number>(0);
  const queryClient = useQueryClient();

  // Fetch data
  const { data: stats } = useQuery({
    queryKey: ['testing-method-stats'],
    queryFn: api.fetchTestingMethodStats
  });

  const { data: projects = [] } = useQuery({
    queryKey: ['projects'],
    queryFn: api.fetchProjects,
    refetchOnMount: 'always'
  });

  const bugFilters = selectedProject !== 'all' 
    ? { status: 'open', limit: 10, project_name: selectedProject } 
    : { status: 'open', limit: 10 };

  const { data: bugs = [] } = useQuery({
    queryKey: ['manual-bugs', selectedProject],
    queryFn: () => api.fetchBugs(bugFilters)
  });

  const { data: automatedContext } = useQuery({
    queryKey: ['automated-context', selectedProject],
    queryFn: () => api.fetchAutomatedContext(selectedProject === 'All Projects' ? undefined : selectedProject),
    refetchOnMount: 'always'
  });
  const hasValidAutomatedSummary = automatedContext?.has_automated_results && (automatedContext.total_violations ?? -1) >= 0;

  const { data: checklist } = useQuery({
    queryKey: ['checklist', selectedTool],
    queryFn: () => api.fetchChecklist(selectedTool!),
    enabled: !!selectedTool
  });

  const testing_methods = [
    {
      tool: 'nvda',
      name: 'NVDA Screen Reader',
      description: 'Test with NVDA to verify screen reader announcements and navigation',
      icon: <Monitor className="w-6 h-6 text-primary" />
    },
    {
      tool: 'keyboard',
      name: 'Keyboard Navigation',
      description: 'Test all functionality with keyboard only - no mouse',
      icon: <Keyboard className="w-6 h-6 text-primary" />
    },
    {
      tool: 'zoom',
      name: 'Zoom / Low Vision',
      description: 'Test at 200-400% zoom and with screen magnifiers',
      icon: <ZoomIn className="w-6 h-6 text-primary" />
    }
  ];

  const handleStartTesting = (tool: string) => {
    setSelectedTool(tool);
  };

  // Quick bug submission mutation
  const quickBugMutation = useMutation({
    mutationFn: async (bugData: any) => {
      const response = await axios.post('/api/manual-testing-v2/bugs', bugData);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['manual-bugs'] });
      toast.success('Bug reported successfully');
    },
    onError: (error: any) => {
      console.error('Bug submission error:', error);
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to report bug';
      toast.error(errorMessage);
    }
  });

  const handleMarkAsFailed = (index: number, item: any) => {
    const newFailed = new Map(failedItems);
    newFailed.set(index, { description: '', showInput: true });
    setFailedItems(newFailed);
    
    // Expand the item to show the quick bug entry
    const newExpanded = new Set(expandedItems);
    newExpanded.add(index);
    setExpandedItems(newExpanded);
  };

  const handleQuickBugSubmit = (index: number, item: any) => {
    const failedItem = failedItems.get(index);
    if (!failedItem || !failedItem.description.trim()) {
      toast.error('Please enter a description');
      return;
    }

    // Capitalize severity to match backend validation
    const severity = item.priority.charAt(0).toUpperCase() + item.priority.slice(1).toLowerCase();
    
    quickBugMutation.mutate({
      wcag_criterion: item.wcag_criterion,
      testing_tool: selectedTool?.toUpperCase() === 'NVDA' ? 'NVDA' : 
                     selectedTool?.toUpperCase() === 'KEYBOARD' ? 'Keyboard' : 
                     selectedTool?.toUpperCase() === 'ZOOM' ? 'Zoom' : 'Other',
      title: `${item.wcag_criterion} - ${item.item_title}`,
      description: failedItem.description,
      expected_behavior: item.expected_result || 'See checklist item',
      actual_behavior: failedItem.description,
      severity: severity,
      project_name: selectedProject !== 'all' ? selectedProject : 'Default Project'
    });

    // Remove from failed items after submission
    const newFailed = new Map(failedItems);
    newFailed.delete(index);
    setFailedItems(newFailed);
  };

  const handleCancelQuickBug = (index: number) => {
    const newFailed = new Map(failedItems);
    newFailed.delete(index);
    setFailedItems(newFailed);
  };

  const handleUpdateQuickBugDescription = (index: number, description: string) => {
    const newFailed = new Map(failedItems);
    const existing = newFailed.get(index);
    if (existing) {
      newFailed.set(index, { ...existing, description });
      setFailedItems(newFailed);
    }
  };

  // Get automated test results for a specific WCAG criterion
  const getAutomatedResultsForCriterion = (wcagCriterion: string) => {
    if (!automatedContext?.issues) return null;
    
    // Match automated issues to WCAG criterion
    const relatedIssues = automatedContext.issues.filter((issue: any) => {
      // Match by WCAG criterion (e.g., "1.1.1")
      return issue.wcag?.includes(wcagCriterion) || 
             issue.tags?.includes(wcagCriterion.replace(/\./g, ''));
    });

    if (relatedIssues.length === 0) {
      // No violations found - check if this criterion was tested
      const testedCount = automatedContext.stats?.total_elements || 0;
      return {
        passed: true,
        count: testedCount,
        issues: []
      };
    }

    return {
      passed: false,
      count: relatedIssues.length,
      issues: relatedIssues.slice(0, 3) // Show top 3
    };
  };

  const handleReportBug = (item?: any) => {
    if (item && selectedTool) {
      setBugPrefillData({
        wcagCriterion: item.wcag_criterion,
        tool: selectedTool,
        itemTitle: item.item_title,
        projectName: selectedProject !== 'all' ? selectedProject : undefined,
      });
    } else {
      setBugPrefillData({
        projectName: selectedProject !== 'all' ? selectedProject : undefined,
      });
    }
    setBugReportOpen(true);
  };

  // Keyboard shortcuts handler
  const handleKeyDown = (e: React.KeyboardEvent, items: any[]) => {
    if (!items || items.length === 0) return;
    const target = e.target as HTMLElement;
    if (target && (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA')) {
      return;
    }

    switch (e.key.toLowerCase()) {
      case 'j':
        e.preventDefault();
        setFocusedItemIndex(prev => Math.min(prev + 1, items.length - 1));
        break;
      case 'k':
        e.preventDefault();
        setFocusedItemIndex(prev => Math.max(prev - 1, 0));
        break;
      case ' ':
        e.preventDefault();
        const newExpanded = new Set(expandedItems);
        if (expandedItems.has(focusedItemIndex)) {
          newExpanded.delete(focusedItemIndex);
        } else {
          newExpanded.add(focusedItemIndex);
        }
        setExpandedItems(newExpanded);
        break;
      case 'f':
        e.preventDefault();
        if (!failedItems.has(focusedItemIndex)) {
          handleMarkAsFailed(focusedItemIndex, items[focusedItemIndex]);
        }
        break;
      case 'r':
        e.preventDefault();
        handleReportBug(items[focusedItemIndex]);
        break;
      case '?':
        e.preventDefault();
        setShowKeyboardHelp(prev => !prev);
        break;
      case 'escape':
        e.preventDefault();
        setSelectedTool(null);
        break;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold">Manual Accessibility Testing</h1>
          <p className="text-muted-foreground mt-1">
            Professional tool-based testing workflow for WCAG 2.1 AA compliance
          </p>
        </div>
        <div className="flex items-center gap-2">
          <FolderKanban className="w-4 h-4 text-muted-foreground" />
          <Select value={selectedProject} onValueChange={setSelectedProject}>
            <SelectTrigger className="w-[200px]">
              <SelectValue placeholder="Select project" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Projects</SelectItem>
              {projects.map((project: string) => (
                <SelectItem key={project} value={project}>
                  {project}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Automated Context Integration */}
      {hasValidAutomatedSummary && (
        <Card className="border-blue-200 bg-blue-50/50 dark:border-blue-800 dark:bg-blue-950/30">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Bot className="w-5 h-5 text-blue-600 dark:text-blue-400" />
              🤖 Automated Scan Results
            </CardTitle>
            <CardDescription>
              Latest: {new Date(automatedContext.scan_time).toLocaleString()}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="text-sm">
                <div className="font-semibold mb-2">Total violations found: {automatedContext.total_violations}</div>
                <div className="space-y-1 ml-4">
                  <div className="flex items-center gap-2 text-green-700 dark:text-green-400">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Auto-verified: {automatedContext.total_violations - automatedContext.manual_verification_count} {automatedContext.manual_verification_count === 0 ? '(no manual test needed)' : ''}</span>
                  </div>
                  <div className="flex items-center gap-2 text-orange-700 dark:text-orange-400">
                    <AlertTriangle className="w-4 h-4" />
                    <span>Needs manual verification: {automatedContext.manual_verification_count}</span>
                  </div>
                </div>
              </div>

              {automatedContext.manual_verification_count > 0 && (
                <div className="pt-2 border-t">
                  <div className="text-sm font-semibold mb-2">Priority manual tests:</div>
                  <div className="text-xs text-muted-foreground ml-4">
                    {automatedContext.priority_items?.slice(0, 3).map((item: any, idx: number) => (
                      <div key={idx}>#{item.index} {item.wcag_criterion} {item.title} ({item.count} violations)</div>
                    )) || 'Select a testing method below to start'}
                  </div>
                </div>
              )}

              <div className="flex gap-2 pt-2">
                <Button variant="outline" size="sm" onClick={() => navigate(`/scan/${automatedContext.scan_id}/issues`)}>
                  View All Violations
                </Button>
                {automatedContext.manual_verification_count > 0 && (
                  <Button variant="default" size="sm">
                    Start Manual Testing
                  </Button>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Testing Method Cards */}
        <div className="lg:col-span-2 space-y-4">
          <h2 className="text-xl font-semibold">Choose Testing Method</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {testing_methods.map((method) => {
              const methodStats = stats?.find((s: any) => s.tool.toLowerCase() === method.tool);
              return (
                <TestingMethodCard
                  key={method.tool}
                  {...method}
                  stats={methodStats}
                  onStart={() => handleStartTesting(method.tool)}
                />
              );
            })}
          </div>

          {/* Checklist View */}
          {selectedTool && checklist && (
            <Card className="mt-6">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>{checklist.name}</CardTitle>
                    <CardDescription>
                      {checklist.description}
                      {checklist.file_info && (
                        <span className="block mt-1 text-xs">
                          {checklist.total_items} items • {checklist.file_info.format} • 
                          Last modified: {new Date(checklist.file_info.last_modified).toLocaleDateString()}
                        </span>
                      )}
                    </CardDescription>
                  </div>
                  <Button variant="outline" size="sm" onClick={() => setSelectedTool(null)}>
                    Close
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <Tabs defaultValue="checklist">
                  <TabsList>
                    <TabsTrigger value="checklist">Checklist ({checklist.total_items || checklist.checklist_items?.length || 0})</TabsTrigger>
                    {checklist.setup_instructions && (
                      <TabsTrigger value="setup">Setup Instructions</TabsTrigger>
                    )}
                    {checklist.common_shortcuts && (
                      <TabsTrigger value="shortcuts">Shortcuts</TabsTrigger>
                    )}
                  </TabsList>

                  <TabsContent value="checklist" className="space-y-4">
                    {/* Filter Controls */}
                    <div className="flex items-center justify-between gap-2 pb-3 border-b">
                      <div className="flex items-center gap-2">
                        <Filter className="w-4 h-4 text-muted-foreground" />
                        <span className="text-sm font-medium">Filter:</span>
                        <Select value={levelFilter} onValueChange={setLevelFilter}>
                          <SelectTrigger className="w-[150px] h-8">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="all">All Levels</SelectItem>
                            <SelectItem value="A">Level A</SelectItem>
                            <SelectItem value="AA">Level AA</SelectItem>
                            <SelectItem value="AAA">Level AAA</SelectItem>
                          </SelectContent>
                        </Select>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            const allIndices = checklist.checklist_items
                              ?.map((_: any, i: number) => i)
                              .filter((i: number) => levelFilter === 'all' || checklist.checklist_items[i].level === levelFilter);
                            // If ANY items are expanded, collapse all. Otherwise expand all.
                            setExpandedItems(expandedItems.size > 0 ? new Set() : new Set(allIndices));
                          }}
                        >
                          {expandedItems.size > 0 ? 'Collapse All' : 'Expand All'}
                        </Button>
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setShowKeyboardHelp(!showKeyboardHelp)}
                      >
                        <Keyboard className="w-4 h-4 mr-1" />
                        Press ? for shortcuts
                      </Button>
                    </div>

                    {/* Keyboard Shortcuts Help */}
                    {showKeyboardHelp && (
                      <div className="p-4 bg-blue-50 border border-blue-200 rounded-md dark:bg-blue-950/30 dark:border-blue-800">
                        <h4 className="font-semibold text-blue-900 mb-3 flex items-center gap-2 dark:text-blue-100">
                          <Keyboard className="w-4 h-4" />
                          Keyboard Shortcuts
                        </h4>
                        <div className="grid grid-cols-2 gap-2 text-sm">
                          <div className="flex items-center gap-2">
                            <Badge variant="secondary" className="font-mono">J</Badge>
                            <span className="text-blue-800 dark:text-blue-200">Next item</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <Badge variant="secondary" className="font-mono">K</Badge>
                            <span className="text-blue-800 dark:text-blue-200">Previous item</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <Badge variant="secondary" className="font-mono">Space</Badge>
                            <span className="text-blue-800 dark:text-blue-200">Expand/Collapse</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <Badge variant="secondary" className="font-mono">F</Badge>
                            <span className="text-blue-800 dark:text-blue-200">Report issue</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <Badge variant="secondary" className="font-mono">R</Badge>
                            <span className="text-blue-800 dark:text-blue-200">Full report</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <Badge variant="secondary" className="font-mono">?</Badge>
                            <span className="text-blue-800 dark:text-blue-200">Toggle this help</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <Badge variant="secondary" className="font-mono">Esc</Badge>
                            <span className="text-blue-800 dark:text-blue-200">Close checklist</span>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Checklist Items */}
                    <div 
                      className="space-y-2 max-h-[500px] overflow-y-auto focus:outline-none" 
                      tabIndex={0}
                      onKeyDown={(e) => handleKeyDown(e, checklist.checklist_items?.filter((item: any) => levelFilter === 'all' || item.level === levelFilter) || [])}
                    >
                      {checklist.checklist_items
                        ?.filter((item: any) => levelFilter === 'all' || item.level === levelFilter)
                        .map((item: any, index: number) => {
                          const isExpanded = expandedItems.has(index);
                          const isFocused = focusedItemIndex === index;
                          const priorityColor = 
                            item.priority === 'Critical' ? 'text-red-700 bg-red-50 border-red-200 dark:text-red-300 dark:bg-red-950/30 dark:border-red-800' :
                            item.priority === 'High' ? 'text-orange-700 bg-orange-50 border-orange-200 dark:text-orange-300 dark:bg-orange-950/30 dark:border-orange-800' :
                            item.priority === 'Medium' ? 'text-yellow-700 bg-yellow-50 border-yellow-200 dark:text-yellow-300 dark:bg-yellow-950/30 dark:border-yellow-800' :
                            'text-blue-700 bg-blue-50 border-blue-200 dark:text-blue-300 dark:bg-blue-950/30 dark:border-blue-800';

                          return (
                            <div
                              key={index}
                              className={`border rounded-lg transition-all ${isExpanded ? 'bg-accent/50' : ''} ${isFocused ? 'ring-2 ring-primary' : ''}`}
                            >
                              {/* Collapsed View */}
                              <div className="p-3 flex items-center gap-3">
                                <Badge variant="outline" className="text-xs font-mono flex-shrink-0 min-w-[2rem] text-center">
                                  #{index + 1}
                                </Badge>
                                <Badge variant="outline" className="text-xs font-mono flex-shrink-0">
                                  {item.wcag_criterion}
                                </Badge>
                                <Badge 
                                  className={`text-xs font-medium flex-shrink-0 ${priorityColor}`}
                                  variant="outline"
                                >
                                  {item.priority}
                                </Badge>
                                <span className="text-sm font-medium flex-1">{item.item_title}</span>
                                {failedItems.has(index) && (
                                  <Badge variant="destructive" className="flex-shrink-0">
                                    <AlertCircle className="w-3 h-3 mr-1" />
                                    Failed
                                  </Badge>
                                )}
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => {
                                    const newExpanded = new Set(expandedItems);
                                    if (isExpanded) {
                                      newExpanded.delete(index);
                                    } else {
                                      newExpanded.add(index);
                                    }
                                    setExpandedItems(newExpanded);
                                  }}
                                  className="flex-shrink-0"
                                >
                                  {isExpanded ? (
                                    <>
                                      <ChevronDown className="w-4 h-4 mr-1" />
                                      Hide Details
                                    </>
                                  ) : (
                                    <>
                                      <ChevronRight className="w-4 h-4 mr-1" />
                                      Show Details
                                    </>
                                  )}
                                </Button>
                                {!failedItems.has(index) && (
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      handleMarkAsFailed(index, item);
                                    }}
                                    className="flex-shrink-0"
                                  >
                                    <AlertCircle className="w-4 h-4 mr-1" />
                                    Report Issue
                                  </Button>
                                )}
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleReportBug(item);
                                  }}
                                  className="flex-shrink-0"
                                >
                                  <Bug className="w-4 h-4 mr-1" />
                                  Full Report
                                </Button>
                              </div>

                              {/* Expanded View */}
                              {isExpanded && (
                                <div className="px-3 pb-3 pt-2 space-y-3 border-t bg-background/50">
                                  {/* Automated Scan Results */}
                                  {(() => {
                                    const automatedResults = getAutomatedResultsForCriterion(item.wcag_criterion);
                                    if (!automatedResults) return null;

                                    return (
                                      <div className={`p-3 rounded-md border ${automatedResults.passed ? 'bg-green-50 border-green-200 dark:bg-green-950/30 dark:border-green-800' : 'bg-orange-50 border-orange-200 dark:bg-orange-950/30 dark:border-orange-800'}`}>
                                        <div className="flex items-start gap-2">
                                          <Bot className={`w-4 h-4 mt-0.5 flex-shrink-0 ${automatedResults.passed ? 'text-green-600 dark:text-green-400' : 'text-orange-600 dark:text-orange-400'}`} />
                                          <div className="flex-1">
                                            <div className={`font-semibold text-sm mb-1 ${automatedResults.passed ? 'text-green-900 dark:text-green-100' : 'text-orange-900 dark:text-orange-100'}`}>
                                              🤖 Automated Scan: {automatedResults.passed ? `PASSED (${automatedResults.count} elements checked)` : `${automatedResults.count} violations found`}
                                            </div>
                                            {!automatedResults.passed && automatedResults.issues.length > 0 && (
                                              <ul className="text-xs text-orange-800 space-y-1 mt-2 dark:text-orange-200">
                                                {automatedResults.issues.map((issue: any, idx: number) => (
                                                  <li key={idx} className="flex items-start gap-1">
                                                    <span className="text-orange-600 flex-shrink-0 dark:text-orange-400">├─</span>
                                                    <span><strong>{issue.context || issue.selector}:</strong> {issue.message || issue.description}</span>
                                                  </li>
                                                ))}
                                              </ul>
                                            )}
                                            <div className="flex gap-2 mt-2">
                                              {!automatedResults.passed ? (
                                                <>
                                                  <Button
                                                    variant="outline"
                                                    size="sm"
                                                    className="h-7 text-xs"
                                                    onClick={(e) => {
                                                      e.stopPropagation();
                                                      if (selectedProject !== 'all') {
                                                        navigate(`/scan/${automatedResults.issues[0]?.run_id}/issues`);
                                                      }
                                                    }}
                                                  >
                                                    View Details
                                                  </Button>
                                                  <Button
                                                    variant="outline"
                                                    size="sm"
                                                    className="h-7 text-xs"
                                                  >
                                                    Test with {selectedTool?.toUpperCase()}
                                                  </Button>
                                                </>
                                              ) : (
                                                <>
                                                  <Button
                                                    variant="outline"
                                                    size="sm"
                                                    className="h-7 text-xs"
                                                    onClick={(e) => {
                                                      e.stopPropagation();
                                                      toast.success('Skipped - automated scan passed');
                                                    }}
                                                  >
                                                    Skip Manual Test
                                                  </Button>
                                                  <Button
                                                    variant="outline"
                                                    size="sm"
                                                    className="h-7 text-xs"
                                                  >
                                                    Test Anyway
                                                  </Button>
                                                </>
                                              )}
                                            </div>
                                          </div>
                                        </div>
                                      </div>
                                    );
                                  })()}

                                  <div>
                                    <div className="text-xs font-semibold text-muted-foreground uppercase mb-1">
                                      Instructions
                                    </div>
                                    <div className="text-sm">{item.instructions}</div>
                                  </div>
                                  
                                  <div>
                                    <div className="text-xs font-semibold text-muted-foreground uppercase mb-1">
                                      Expected Result
                                    </div>
                                    <div className="text-sm text-muted-foreground">{item.expected_result}</div>
                                  </div>
                                  
                                  <div>
                                    <div className="text-xs font-semibold text-muted-foreground uppercase mb-1">
                                      Common Failures
                                    </div>
                                    <div className="text-sm text-muted-foreground">{item.common_failures}</div>
                                  </div>
                                  
                                  {/* Contextual Testing Resources */}
                                  <div className="pt-2 border-t">
                                    <div className="text-xs font-semibold text-muted-foreground uppercase mb-2">
                                      Quick Help
                                    </div>
                                    <div className="flex flex-col gap-2">
                                      {item.reference_url && (
                                        <a 
                                          href={item.reference_url} 
                                          target="_blank" 
                                          rel="noopener noreferrer"
                                          className="text-xs text-muted-foreground hover:text-primary inline-flex items-center gap-1"
                                          onClick={(e) => e.stopPropagation()}
                                        >
                                          <ExternalLink className="w-3 h-3" />
                                          🔗 WCAG {item.wcag_criterion} Reference
                                        </a>
                                      )}
                                      {selectedTool && (
                                        <a 
                                          href={
                                            selectedTool.toLowerCase() === 'nvda' 
                                              ? 'https://webaim.org/articles/nvda/' 
                                              : selectedTool.toLowerCase() === 'keyboard'
                                              ? 'https://webaim.org/articles/keyboard/'
                                              : selectedTool.toLowerCase() === 'zoom'
                                              ? 'https://webaim.org/articles/visual/'
                                              : 'https://webaim.org/'
                                          }
                                          target="_blank" 
                                          rel="noopener noreferrer"
                                          className="text-xs text-muted-foreground hover:text-primary inline-flex items-center gap-1"
                                          onClick={(e) => e.stopPropagation()}
                                        >
                                          <ExternalLink className="w-3 h-3" />
                                          🔗 {selectedTool.toUpperCase()} Testing Guide
                                        </a>
                                      )}
                                    </div>
                                  </div>

                                  {/* Quick Bug Entry (only shown when failed) */}
                                  {failedItems.has(index) && (
                                    <div className="pt-3 border-t space-y-2" onClick={(e) => e.stopPropagation()}>
                                      <div className="flex items-start gap-2">
                                        <div className="flex-1">
                                          <label className="text-xs font-semibold text-muted-foreground uppercase block mb-1">
                                            Quick Bug Description
                                          </label>
                                          <textarea
                                            className="w-full px-3 py-2 text-sm border rounded-md resize-none focus:outline-none focus:ring-2 focus:ring-primary"
                                            rows={2}
                                            placeholder="e.g., Email field missing label"
                                            value={failedItems.get(index)?.description || ''}
                                            onChange={(e) => handleUpdateQuickBugDescription(index, e.target.value)}
                                            autoFocus
                                          />
                                        </div>
                                        <Button
                                          variant="ghost"
                                          size="sm"
                                          onClick={() => handleCancelQuickBug(index)}
                                          className="mt-6"
                                        >
                                          <X className="w-4 h-4" />
                                        </Button>
                                      </div>
                                      <div className="flex items-center gap-2">
                                        <Button
                                          size="sm"
                                          onClick={() => handleQuickBugSubmit(index, item)}
                                          disabled={quickBugMutation.isPending}
                                        >
                                          Submit Bug
                                        </Button>
                                        <Button
                                          variant="outline"
                                          size="sm"
                                          onClick={() => {
                                            handleCancelQuickBug(index);
                                            handleReportBug(item);
                                          }}
                                        >
                                          Need More Details
                                        </Button>
                                        <span className="text-xs text-muted-foreground">
                                          Simple bugs only need 1 sentence
                                        </span>
                                      </div>
                                    </div>
                                  )}
                                </div>
                              )}
                            </div>
                          );
                        })}
                    </div>
                  </TabsContent>

                  <TabsContent value="setup">
                    <div className="space-y-2">
                      <h4 className="font-medium">Setup Instructions</h4>
                      <ul className="list-disc list-inside space-y-1 text-sm">
                        {checklist.setup_instructions?.map((instruction: string, i: number) => (
                          <li key={i}>{instruction}</li>
                        ))}
                      </ul>
                    </div>
                  </TabsContent>

                  <TabsContent value="shortcuts">
                    <div className="space-y-2">
                      <h4 className="font-medium">Common Shortcuts</h4>
                      <div className="grid grid-cols-2 gap-2 text-sm">
                        {Object.entries(checklist.common_shortcuts || {}).map(([key, value]) => (
                          <div key={key} className="flex items-start gap-2">
                            <Badge variant="secondary" className="text-xs">{key}</Badge>
                            <span className="text-xs text-muted-foreground">{value as string}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Right Column: Recent Bugs */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">Recent Bugs</h2>
            <Button onClick={handleReportBug} size="sm">
              <Plus className="w-4 h-4 mr-1" />
              Report Bug
            </Button>
          </div>

          <div className="space-y-3">
            {bugs.length === 0 ? (
              <Card>
                <CardContent className="pt-6 text-center text-muted-foreground">
                  <Bug className="w-12 h-12 mx-auto mb-3 opacity-20" />
                  <p className="text-sm">No bugs reported yet</p>
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={handleReportBug}
                    className="mt-3"
                  >
                    Report First Bug
                  </Button>
                </CardContent>
              </Card>
            ) : (
              bugs.map((bug: any) => (
                <BugItem
                  key={bug.id}
                  bug={bug}
                  onClick={() => navigate(`/manual-testing-v2/bugs/${bug.id}`)}
                />
              ))
            )}
          </div>

          <Button 
            variant="outline" 
            className="w-full" 
            onClick={() => navigate('/manual-testing-v2/bugs')}
          >
            View All Bugs
          </Button>
        </div>
      </div>

      <BugReportDialog
        open={bugReportOpen}
        onOpenChange={setBugReportOpen}
        prefillData={bugPrefillData}
      />
    </div>
  );
}
