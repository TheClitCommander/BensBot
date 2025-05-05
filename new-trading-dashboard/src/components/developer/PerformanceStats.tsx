import React from 'react';

interface ModulePerformance {
  name: string;
  cpuUsage: number;
  memoryUsage: number;
  status: 'High' | 'Elevated' | 'Normal' | 'Low';
}

interface ApiCallStats {
  count: number;
  avg_latency: number;
  errors: number;
}

interface PerformanceData {
  cpuUsage: number;
  memoryUsage: number;
  diskUsage: number;
  networkUsage: number;
  requestLatency: number;
  databaseQueries: number;
  activeUsers: number;
  modulePerformance: ModulePerformance[];
  apiCallStats: {
    [key: string]: ApiCallStats;
  };
}

const PerformanceStats: React.FC = () => {
  // Mock data for system performance - in production would connect to system monitoring APIs
  const performanceData: PerformanceData = {
    cpuUsage: 42,
    memoryUsage: 68,
    diskUsage: 54,
    networkUsage: 31,
    requestLatency: 124, // milliseconds
    databaseQueries: 782,
    activeUsers: 1,
    modulePerformance: [
      { name: 'Strategy Manager', cpuUsage: 18, memoryUsage: 12, status: 'Normal' },
      { name: 'Data Provider', cpuUsage: 25, memoryUsage: 28, status: 'High' },
      { name: 'Backtester', cpuUsage: 65, memoryUsage: 45, status: 'Elevated' },
      { name: 'AI Coordinator', cpuUsage: 32, memoryUsage: 22, status: 'Normal' },
      { name: 'Order Manager', cpuUsage: 8, memoryUsage: 5, status: 'Low' },
      { name: 'Risk Manager', cpuUsage: 12, memoryUsage: 8, status: 'Normal' }
    ],
    apiCallStats: {
      market_data: { count: 342, avg_latency: 215, errors: 3 },
      news_api: { count: 128, avg_latency: 310, errors: 1 },
      broker_api: { count: 87, avg_latency: 150, errors: 0 },
      ai_services: { count: 95, avg_latency: 450, errors: 2 }
    }
  };

  return (
    <div className="dashboard-grid">
      <div className="card">
        <h2 className="card-header">System Performance</h2>
        <div className="card-content">
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '24px',
            marginBottom: '24px'
          }}>
            {/* CPU Usage */}
            <div style={{ textAlign: 'center' }}>
              <div 
                style={{ 
                  width: '120px',
                  height: '120px',
                  margin: '0 auto',
                  borderRadius: '50%',
                  background: `conic-gradient(
                    ${performanceData.cpuUsage > 80 ? '#F44336' : performanceData.cpuUsage > 60 ? '#FF9800' : '#4CAF50'} 
                    ${performanceData.cpuUsage * 3.6}deg, 
                    #333 0deg
                  )`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  position: 'relative',
                  marginBottom: '8px'
                }}
              >
                <div 
                  style={{ 
                    width: '90px',
                    height: '90px',
                    borderRadius: '50%',
                    backgroundColor: '#1e1e1e',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '1.5rem',
                    fontWeight: 'bold',
                    color: performanceData.cpuUsage > 80 ? '#F44336' : performanceData.cpuUsage > 60 ? '#FF9800' : '#4CAF50'
                  }}
                >
                  {performanceData.cpuUsage}%
                </div>
              </div>
              <div style={{ fontWeight: 'bold' }}>CPU Usage</div>
            </div>
            
            {/* Memory Usage */}
            <div style={{ textAlign: 'center' }}>
              <div 
                style={{ 
                  width: '120px',
                  height: '120px',
                  margin: '0 auto',
                  borderRadius: '50%',
                  background: `conic-gradient(
                    ${performanceData.memoryUsage > 80 ? '#F44336' : performanceData.memoryUsage > 60 ? '#FF9800' : '#4CAF50'} 
                    ${performanceData.memoryUsage * 3.6}deg, 
                    #333 0deg
                  )`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  position: 'relative',
                  marginBottom: '8px'
                }}
              >
                <div 
                  style={{ 
                    width: '90px',
                    height: '90px',
                    borderRadius: '50%',
                    backgroundColor: '#1e1e1e',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '1.5rem',
                    fontWeight: 'bold',
                    color: performanceData.memoryUsage > 80 ? '#F44336' : performanceData.memoryUsage > 60 ? '#FF9800' : '#4CAF50'
                  }}
                >
                  {performanceData.memoryUsage}%
                </div>
              </div>
              <div style={{ fontWeight: 'bold' }}>Memory Usage</div>
            </div>
            
            {/* Disk Usage */}
            <div style={{ textAlign: 'center' }}>
              <div 
                style={{ 
                  width: '120px',
                  height: '120px',
                  margin: '0 auto',
                  borderRadius: '50%',
                  background: `conic-gradient(
                    ${performanceData.diskUsage > 80 ? '#F44336' : performanceData.diskUsage > 60 ? '#FF9800' : '#4CAF50'} 
                    ${performanceData.diskUsage * 3.6}deg, 
                    #333 0deg
                  )`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  position: 'relative',
                  marginBottom: '8px'
                }}
              >
                <div 
                  style={{ 
                    width: '90px',
                    height: '90px',
                    borderRadius: '50%',
                    backgroundColor: '#1e1e1e',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '1.5rem',
                    fontWeight: 'bold',
                    color: performanceData.diskUsage > 80 ? '#F44336' : performanceData.diskUsage > 60 ? '#FF9800' : '#4CAF50'
                  }}
                >
                  {performanceData.diskUsage}%
                </div>
              </div>
              <div style={{ fontWeight: 'bold' }}>Disk Usage</div>
            </div>
            
            {/* Network Usage */}
            <div style={{ textAlign: 'center' }}>
              <div 
                style={{ 
                  width: '120px',
                  height: '120px',
                  margin: '0 auto',
                  borderRadius: '50%',
                  background: `conic-gradient(
                    ${performanceData.networkUsage > 80 ? '#F44336' : performanceData.networkUsage > 60 ? '#FF9800' : '#4CAF50'} 
                    ${performanceData.networkUsage * 3.6}deg, 
                    #333 0deg
                  )`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  position: 'relative',
                  marginBottom: '8px'
                }}
              >
                <div 
                  style={{ 
                    width: '90px',
                    height: '90px',
                    borderRadius: '50%',
                    backgroundColor: '#1e1e1e',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '1.5rem',
                    fontWeight: 'bold',
                    color: performanceData.networkUsage > 80 ? '#F44336' : performanceData.networkUsage > 60 ? '#FF9800' : '#4CAF50'
                  }}
                >
                  {performanceData.networkUsage}%
                </div>
              </div>
              <div style={{ fontWeight: 'bold' }}>Network Usage</div>
            </div>
          </div>
          
          <div 
            style={{ 
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: '24px',
              marginBottom: '24px'
            }}
          >
            <div>
              <h3>System Stats</h3>
              <div 
                style={{ 
                  padding: '16px',
                  backgroundColor: '#272727',
                  borderRadius: '8px'
                }}
              >
                <div style={{ marginBottom: '16px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                    <span>Request Latency</span>
                    <span>{performanceData.requestLatency} ms</span>
                  </div>
                  <div className="progress-bar">
                    <div 
                      className={`progress-bar-fill ${
                        performanceData.requestLatency > 200 ? 'danger' : 
                        performanceData.requestLatency > 100 ? 'warning' : 'success'
                      }`}
                      style={{ width: `${Math.min(100, performanceData.requestLatency / 3)}%` }}
                    />
                  </div>
                </div>
                
                <div style={{ marginBottom: '16px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                    <span>Database Queries</span>
                    <span>{performanceData.databaseQueries}</span>
                  </div>
                  <div className="progress-bar">
                    <div 
                      className="progress-bar-fill info"
                      style={{ width: `${Math.min(100, performanceData.databaseQueries / 10)}%` }}
                    />
                  </div>
                </div>
                
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                    <span>Active Users</span>
                    <span>{performanceData.activeUsers}</span>
                  </div>
                  <div className="progress-bar">
                    <div 
                      className="progress-bar-fill success"
                      style={{ width: `${Math.min(100, performanceData.activeUsers * 10)}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>
            
            <div>
              <h3>Active Processes</h3>
              <div 
                style={{ 
                  padding: '16px',
                  backgroundColor: '#272727',
                  borderRadius: '8px',
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'center',
                  alignItems: 'center',
                  gap: '16px'
                }}
              >
                <div style={{ 
                  display: 'flex',
                  justifyContent: 'center',
                  alignItems: 'center',
                  width: '120px',
                  height: '120px',
                  border: '8px solid #4F8BFF',
                  borderRadius: '50%',
                  fontSize: '2.5rem',
                  fontWeight: 'bold'
                }}>
                  12
                </div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '0.9rem', color: '#9e9e9e' }}>Running Processes</div>
                  <div style={{ fontSize: '0.8rem', color: '#4CAF50', marginTop: '4px' }}>All Systems Operational</div>
                </div>
              </div>
            </div>
          </div>
          
          <h3>Module Performance</h3>
          <div style={{ 
            backgroundColor: '#272727',
            borderRadius: '8px',
            padding: '16px',
            marginBottom: '24px'
          }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ textAlign: 'left', borderBottom: '1px solid #444' }}>
                  <th style={{ padding: '8px' }}>Module</th>
                  <th style={{ padding: '8px' }}>CPU Usage</th>
                  <th style={{ padding: '8px' }}>Memory Usage</th>
                  <th style={{ padding: '8px' }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {performanceData.modulePerformance.map((module, index) => (
                  <tr 
                    key={index}
                    style={{ 
                      borderBottom: index === performanceData.modulePerformance.length - 1 ? 'none' : '1px solid #333'
                    }}
                  >
                    <td style={{ padding: '12px 8px' }}>{module.name}</td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <div className="progress-bar" style={{ flex: 1, margin: 0 }}>
                          <div 
                            className={`progress-bar-fill ${
                              module.cpuUsage > 60 ? 'danger' : 
                              module.cpuUsage > 30 ? 'warning' : 'success'
                            }`}
                            style={{ width: `${module.cpuUsage}%` }}
                          />
                        </div>
                        <span>{module.cpuUsage}%</span>
                      </div>
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <div className="progress-bar" style={{ flex: 1, margin: 0 }}>
                          <div 
                            className={`progress-bar-fill ${
                              module.memoryUsage > 40 ? 'danger' : 
                              module.memoryUsage > 20 ? 'warning' : 'success'
                            }`}
                            style={{ width: `${module.memoryUsage}%` }}
                          />
                        </div>
                        <span>{module.memoryUsage}%</span>
                      </div>
                    </td>
                    <td>
                      <span className={`badge ${
                        module.status === 'High' ? 'danger' : 
                        module.status === 'Elevated' ? 'warning' : 
                        module.status === 'Normal' ? 'info' : 'success'
                      }`}>
                        {module.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
          <h3>API Performance</h3>
          <div className="dashboard-grid" style={{ marginBottom: '16px' }}>
            {Object.entries(performanceData.apiCallStats).map(([apiName, stats]) => (
              <div 
                key={apiName} 
                style={{ 
                  backgroundColor: '#272727',
                  padding: '16px',
                  borderRadius: '8px'
                }}
              >
                <h4 style={{ marginTop: 0, marginBottom: '12px' }}>
                  {apiName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </h4>
                
                <div style={{ 
                  display: 'grid', 
                  gridTemplateColumns: 'repeat(3, 1fr)',
                  gap: '12px',
                  textAlign: 'center'
                }}>
                  <div>
                    <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>
                      {stats.count}
                    </div>
                    <div style={{ fontSize: '0.8rem', color: '#9e9e9e' }}>Requests</div>
                  </div>
                  <div>
                    <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>
                      {stats.avg_latency}ms
                    </div>
                    <div style={{ fontSize: '0.8rem', color: '#9e9e9e' }}>Avg. Latency</div>
                  </div>
                  <div>
                    <div style={{ 
                      fontSize: '1.5rem', 
                      fontWeight: 'bold',
                      color: stats.errors > 0 ? '#F44336' : '#4CAF50'
                    }}>
                      {stats.errors}
                    </div>
                    <div style={{ fontSize: '0.8rem', color: '#9e9e9e' }}>Errors</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
          
          <div style={{ textAlign: 'center' }}>
            <button
              style={{
                backgroundColor: '#4F8BFF',
                border: 'none',
                padding: '8px 16px',
                borderRadius: '4px',
                color: 'white',
                cursor: 'pointer'
              }}
            >
              Generate Performance Report
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PerformanceStats;
