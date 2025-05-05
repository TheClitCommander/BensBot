import React from 'react';

const PerformanceStats = () => {
  // Mock data for system performance
  const performanceData = {
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
          
          <h3>Key Metrics</h3>
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '16px',
            marginBottom: '24px'
          }}>
            <div style={{ 
              backgroundColor: '#272727',
              padding: '16px',
              borderRadius: '8px',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#4F8BFF' }}>
                {performanceData.requestLatency}ms
              </div>
              <div style={{ color: '#9e9e9e' }}>Avg. Request Latency</div>
            </div>
            
            <div style={{ 
              backgroundColor: '#272727',
              padding: '16px',
              borderRadius: '8px',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#4F8BFF' }}>
                {performanceData.databaseQueries}
              </div>
              <div style={{ color: '#9e9e9e' }}>Database Queries</div>
            </div>
            
            <div style={{ 
              backgroundColor: '#272727',
              padding: '16px',
              borderRadius: '8px',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#4F8BFF' }}>
                {performanceData.activeUsers}
              </div>
              <div style={{ color: '#9e9e9e' }}>Active Users</div>
            </div>
          </div>
          
          <h3>Module Performance</h3>
          <div className="table-container" style={{ marginBottom: '24px' }}>
            <table>
              <thead>
                <tr>
                  <th>Module</th>
                  <th>CPU Usage</th>
                  <th>Memory Usage</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {performanceData.modulePerformance.map((module, index) => (
                  <tr key={index}>
                    <td>{module.name}</td>
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
