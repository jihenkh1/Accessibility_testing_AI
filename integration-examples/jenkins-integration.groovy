// Example: Jenkins Pipeline Integration
// Place this in your testing project's Jenkinsfile

pipeline {
    agent any
    
    environment {
        DASHBOARD_API = credentials('a11y-dashboard-url')
        DASHBOARD_KEY = credentials('a11y-dashboard-key')
    }
    
    stages {
        stage('Run Accessibility Tests') {
            steps {
                sh 'npm run test:accessibility'
            }
        }
        
        stage('Send to AI Dashboard') {
            steps {
                script {
                    def response = sh(
                        script: """
                            curl -X POST "\${DASHBOARD_API}/api/scans" \\
                              -H "Content-Type: application/json" \\
                              -H "Authorization: Bearer \${DASHBOARD_KEY}" \\
                              -d @./reports/axe-results.json
                        """,
                        returnStdout: true
                    ).trim()
                    
                    def json = readJSON text: response
                    def scanId = json.scan_id
                    def dashboardUrl = "${DASHBOARD_API}/scan/${scanId}"
                    
                    echo "Dashboard: ${dashboardUrl}"
                    currentBuild.description = "<a href='${dashboardUrl}'>View A11y Report</a>"
                    
                    // Fail if critical issues
                    if (json.summary.critical_issues > 0) {
                        error("Found ${json.summary.critical_issues} critical accessibility issues")
                    }
                }
            }
        }
    }
    
    post {
        always {
            archiveArtifacts artifacts: 'reports/**/*.json', allowEmptyArchive: true
        }
    }
}
