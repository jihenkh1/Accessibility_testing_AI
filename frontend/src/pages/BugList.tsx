import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Search, ArrowLeft, FileText } from 'lucide-react';

interface Bug {
  id: number;
  title: string;
  wcag_criterion: string;
  severity: string;
  testing_tool: string;
  status: string;
  created_at: string;
  project_name: string;
  evidence_count: number;
}

async function fetchBugs(filters: any) {
  const params = new URLSearchParams();
  if (filters.status && filters.status !== 'all') params.append('status', filters.status);
  if (filters.severity && filters.severity !== 'all') params.append('severity', filters.severity);
  if (filters.tool && filters.tool !== 'all') params.append('testing_tool', filters.tool);
  if (filters.project) params.append('project_name', filters.project);
  if (filters.search) params.append('search', filters.search);
  
  const res = await axios.get(`/api/manual-testing-v2/bugs?${params}`);
  return res.data;
}

function BugList() {
  const navigate = useNavigate();
  const [filters, setFilters] = useState({
    status: 'all',
    severity: 'all',
    tool: 'all',
    project: '',
    search: '',
  });

  const { data: bugs = [], isLoading, error } = useQuery({
    queryKey: ['bugs', filters],
    queryFn: () => fetchBugs(filters),
  });

  if (isLoading) {
    return (
      <div className="p-6 max-w-[1600px] mx-auto">
        <div className="text-center py-12">
          <p className="text-muted-foreground">Loading bugs...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 max-w-[1600px] mx-auto">
        <div className="text-center py-12">
          <p className="text-destructive">Error loading bugs: {(error as Error).message}</p>
          <Button onClick={() => navigate('/manual-testing')} className="mt-4">
            Back to Dashboard
          </Button>
        </div>
      </div>
    );
  }

  const severityColors: Record<string, 'destructive' | 'default' | 'secondary'> = {
    Critical: 'destructive',
    High: 'destructive',
    Medium: 'default',
    Low: 'secondary',
  };

  const statusColors: Record<string, 'destructive' | 'default' | 'secondary' | 'outline'> = {
    open: 'destructive',
    in_progress: 'default',
    resolved: 'secondary',
    closed: 'outline',
  };

  const hasActiveFilters = filters.status !== 'all' || filters.severity !== 'all' || 
                          filters.tool !== 'all' || filters.project || filters.search;

  return (
    <div className="p-6 max-w-[1600px] mx-auto">
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" onClick={() => navigate('/manual-testing')}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Dashboard
          </Button>
          <div>
            <h1 className="text-3xl font-bold">Bug Reports</h1>
            <p className="text-muted-foreground">
              {bugs.length} {bugs.length === 1 ? 'bug' : 'bugs'} found
            </p>
          </div>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Filters</CardTitle>
          <CardDescription>Filter and search bug reports</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                placeholder="Search title, WCAG..."
                value={filters.search}
                onChange={e => setFilters({ ...filters, search: e.target.value })}
                className="pl-9"
              />
            </div>

            <Select value={filters.status} onValueChange={value => setFilters({ ...filters, status: value })}>
              <SelectTrigger>
                <SelectValue placeholder="All Statuses" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Statuses</SelectItem>
                <SelectItem value="open">Open</SelectItem>
                <SelectItem value="in_progress">In Progress</SelectItem>
                <SelectItem value="resolved">Resolved</SelectItem>
                <SelectItem value="closed">Closed</SelectItem>
              </SelectContent>
            </Select>

            <Select value={filters.severity} onValueChange={value => setFilters({ ...filters, severity: value })}>
              <SelectTrigger>
                <SelectValue placeholder="All Severities" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Severities</SelectItem>
                <SelectItem value="Critical">Critical</SelectItem>
                <SelectItem value="High">High</SelectItem>
                <SelectItem value="Medium">Medium</SelectItem>
                <SelectItem value="Low">Low</SelectItem>
              </SelectContent>
            </Select>

            <Select value={filters.tool} onValueChange={value => setFilters({ ...filters, tool: value })}>
              <SelectTrigger>
                <SelectValue placeholder="All Tools" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Tools</SelectItem>
                <SelectItem value="NVDA">NVDA</SelectItem>
                <SelectItem value="Keyboard">Keyboard</SelectItem>
                <SelectItem value="Zoom">Zoom</SelectItem>
                <SelectItem value="Other">Other</SelectItem>
              </SelectContent>
            </Select>

            <Input
              placeholder="Project name"
              value={filters.project}
              onChange={e => setFilters({ ...filters, project: e.target.value })}
            />
          </div>

          {hasActiveFilters && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setFilters({ status: 'all', severity: 'all', tool: 'all', project: '', search: '' })}
              className="mt-2"
            >
              Clear Filters
            </Button>
          )}
        </CardContent>
      </Card>

      <Card className="mt-6">
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-8 text-center text-muted-foreground">Loading bugs...</div>
          ) : bugs.length === 0 ? (
            <div className="p-8 text-center text-muted-foreground">
              <FileText className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>No bugs found matching your filters.</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Title</TableHead>
                  <TableHead>WCAG</TableHead>
                  <TableHead>Severity</TableHead>
                  <TableHead>Tool</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Project</TableHead>
                  <TableHead>Evidence</TableHead>
                  <TableHead>Created</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {bugs.map((bug: Bug) => (
                  <TableRow
                    key={bug.id}
                    className="cursor-pointer hover:bg-muted/50"
                    onClick={() => navigate(`/manual-testing-v2/bugs/${bug.id}`)}
                  >
                    <TableCell className="font-medium max-w-md truncate">{bug.title}</TableCell>
                    <TableCell>
                      <Badge variant="outline">{bug.wcag_criterion}</Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant={severityColors[bug.severity] as any}>{bug.severity}</Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant="secondary">{bug.testing_tool}</Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant={statusColors[bug.status] as any}>
                        {bug.status.replace('_', ' ')}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">{bug.project_name}</TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {bug.evidence_count > 0 && `${bug.evidence_count} file${bug.evidence_count !== 1 ? 's' : ''}`}
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {new Date(bug.created_at).toLocaleDateString()}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default BugList;
