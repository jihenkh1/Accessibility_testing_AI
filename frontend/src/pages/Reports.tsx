import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { listScans, deleteScan } from '../lib/api';
import { FileText, Calendar, ExternalLink, Download, Search, Filter, Eye, X, Trash2 } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';

type ViewerModal = {
  scanId: number;
  type: 'pdf' | 'html';
  title: string;
} | null;

export default function Reports() {
  const queryClient = useQueryClient();
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState<'all' | 'pdf' | 'html' | 'both'>('all');
  const [viewer, setViewer] = useState<ViewerModal>(null);

  const { data: scans, isLoading } = useQuery({
    queryKey: ['scans'],
    queryFn: listScans,
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: deleteScan,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scans'] })
      queryClient.invalidateQueries({ queryKey: ['fixMetrics'] })
    }
  });

  const handleDelete = (scanId: number, event: React.MouseEvent) => {
    event.preventDefault();
    event.stopPropagation();
    if (confirm('Are you sure you want to delete this report? This action cannot be undone.')) {
      deleteMutation.mutate(scanId);
    }
  };

  // Filter scans that have report artifacts
  const reportsWithArtifacts = scans?.filter(scan => 
    scan.pdf_report_path || scan.html_report_path
  ) || [];

  // Separate documentation reports from accessibility reports
  const documentationReports = reportsWithArtifacts.filter(scan => 
    scan.framework === 'documentation' || scan.total_issues === -1
  );
  
  const accessibilityReports = reportsWithArtifacts.filter(scan => 
    scan.framework !== 'documentation' && scan.total_issues !== -1
  );

  // Apply search and filter
  const allReports = [...documentationReports, ...accessibilityReports];
  
  const filteredReports = allReports.filter(scan => {
    const matchesSearch = scan.url?.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesFilter = 
      filterType === 'all' ||
      (filterType === 'pdf' && scan.pdf_report_path) ||
      (filterType === 'html' && scan.html_report_path) ||
      (filterType === 'both' && scan.pdf_report_path && scan.html_report_path);

    return matchesSearch && matchesFilter;
  });

  const handleDownload = (scanId: number, type: 'pdf' | 'html') => {
    const url = `http://localhost:8000/api/scans/${scanId}/${type}-report?download=true`;
    window.open(url, '_blank');
  };

  const handleView = (scanId: number, type: 'pdf' | 'html', title: string) => {
    setViewer({ scanId, type, title });
  };

  const formatDate = (isoString: string) => {
    return new Date(isoString).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Test Reports</h1>
            <p className="text-muted-foreground">
              View and download accessibility test reports
            </p>
          </div>
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map(i => (
            <Card key={i} className="animate-pulse">
              <CardHeader className="h-24 bg-muted" />
              <CardContent className="h-32 bg-muted/50" />
            </Card>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Test Reports</h1>
          <p className="text-muted-foreground">
            View and download uploaded accessibility test reports
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="secondary" className="text-lg px-3 py-1">
            {reportsWithArtifacts.length} Reports
          </Badge>
        </div>
      </div>

      {/* Search and Filter Bar */}
      <div className="flex gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <label htmlFor="search-reports" className="sr-only">Search reports</label>
          <Input
            id="search-reports"
            placeholder="Search by scenario name or URL..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-9"
          />
        </div>
        <label htmlFor="filter-report-type" className="sr-only">Filter by report type</label>
        <Select value={filterType} onValueChange={(value: any) => setFilterType(value)}>
          <SelectTrigger id="filter-report-type" className="w-[180px]">
            <Filter className="h-4 w-4 mr-2" />
            <SelectValue placeholder="Filter by type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Reports</SelectItem>
            <SelectItem value="pdf">PDF Only</SelectItem>
            <SelectItem value="html">HTML Only</SelectItem>
            <SelectItem value="both">Both PDF & HTML</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Documentation Reports</CardDescription>
            <CardTitle className="text-3xl">{documentationReports.length}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Accessibility Reports</CardDescription>
            <CardTitle className="text-3xl">{accessibilityReports.length}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>With PDF</CardDescription>
            <CardTitle className="text-3xl">
              {reportsWithArtifacts.filter(s => s.pdf_report_path).length}
            </CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>With HTML</CardDescription>
            <CardTitle className="text-3xl">
              {reportsWithArtifacts.filter(s => s.html_report_path).length}
            </CardTitle>
          </CardHeader>
        </Card>
      </div>

      {/* Reports Grid */}
      {filteredReports.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <FileText className="mx-auto h-12 w-12 text-muted-foreground/50 mb-4" />
            <h3 className="text-lg font-semibold mb-2">No reports found</h3>
            <p className="text-muted-foreground">
              {searchTerm || filterType !== 'all' 
                ? 'Try adjusting your search or filter criteria'
                : 'Upload test reports to see them here'}
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filteredReports.map((scan) => (
            <Card key={scan.id} className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <FileText className="h-5 w-5 text-primary" />
                  <div className="flex gap-1">
                    {scan.framework === 'documentation' || scan.total_issues === -1 ? (
                      <Badge className="text-xs bg-blue-500">Documentation</Badge>
                    ) : (
                      <Badge variant="outline" className="text-xs">Accessibility</Badge>
                    )}
                  </div>
                </div>
                <CardTitle className="text-lg line-clamp-2">
                  {scan.url || scan.name || `Report #${scan.id}`}
                </CardTitle>
                <CardDescription className="flex items-center gap-1.5 text-xs">
                  <Calendar className="h-3 w-3" />
                  {formatDate(scan.ts)}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center gap-2">
                  {scan.pdf_report_path && (
                    <Badge variant="secondary" className="text-xs">
                      <Download className="h-3 w-3 mr-1" />
                      PDF
                    </Badge>
                  )}
                  {scan.html_report_path && (
                    <Badge variant="secondary" className="text-xs">
                      <Download className="h-3 w-3 mr-1" />
                      HTML
                    </Badge>
                  )}
                </div>
                
                {scan.framework !== 'documentation' && scan.total_issues !== -1 && (
                  <div className="flex items-center gap-2 text-sm">
                    <Badge variant="outline" className="font-mono text-xs">
                      {scan.framework.toUpperCase()}
                    </Badge>
                    {scan.total_issues > 0 && (
                      <Badge variant="outline" className="text-xs">
                        {scan.total_issues} issues found
                      </Badge>
                    )}
                  </div>
                )}

                <div className="space-y-2 pt-2">
                  {/* View Buttons */}
                  <div className="flex gap-2">
                    {scan.pdf_report_path && (
                      <Button
                        size="sm"
                        className="flex-1"
                        onClick={() => handleView(scan.id, 'pdf', scan.url || scan.name || `Report #${scan.id}`)}
                      >
                        <Eye className="h-3.5 w-3.5 mr-1.5" />
                        View PDF
                      </Button>
                    )}
                    {scan.html_report_path && (
                      <Button
                        size="sm"
                        className="flex-1"
                        onClick={() => handleView(scan.id, 'html', scan.url || scan.name || `Report #${scan.id}`)}
                      >
                        <Eye className="h-3.5 w-3.5 mr-1.5" />
                        View HTML
                      </Button>
                    )}
                  </div>
                  
                  {/* Download Buttons */}
                  <div className="flex gap-2">
                    {scan.pdf_report_path && (
                      <Button
                        size="sm"
                        variant="outline"
                        className="flex-1"
                        onClick={() => handleDownload(scan.id, 'pdf')}
                      >
                        <Download className="h-3.5 w-3.5 mr-1.5" />
                        Download PDF
                      </Button>
                    )}
                    {scan.html_report_path && (
                      <Button
                        size="sm"
                        variant="outline"
                        className="flex-1"
                        onClick={() => handleDownload(scan.id, 'html')}
                      >
                        <Download className="h-3.5 w-3.5 mr-1.5" />
                        Download HTML
                      </Button>
                    )}
                  </div>

                  {/* Delete Button */}
                  <Button
                    size="sm"
                    variant="outline"
                    className="w-full text-destructive hover:bg-destructive/10 hover:text-destructive border-destructive/30"
                    onClick={(e) => handleDelete(scan.id, e)}
                    disabled={deleteMutation.isPending}
                  >
                    <Trash2 className="h-3.5 w-3.5 mr-1.5" />
                    Delete Report
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Report Viewer Modal */}
      {viewer && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-background rounded-lg shadow-xl w-full h-full max-w-7xl max-h-[90vh] flex flex-col">
            {/* Modal Header */}
            <div className="flex items-center justify-between p-4 border-b">
              <div className="flex items-center gap-3">
                <FileText className="h-5 w-5 text-primary" />
                <div>
                  <h2 className="font-semibold text-lg">{viewer.title}</h2>
                  <p className="text-sm text-muted-foreground">
                    {viewer.type.toUpperCase()} Report
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleDownload(viewer.scanId, viewer.type)}
                >
                  <Download className="h-4 w-4 mr-2" />
                  Download
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => setViewer(null)}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </div>

            {/* Modal Content - iframe viewer */}
            <div className="flex-1 overflow-hidden">
              <iframe
                src={`http://localhost:8000/api/scans/${viewer.scanId}/${viewer.type}-report`}
                className="w-full h-full border-0"
                title={`${viewer.type} report viewer`}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
