import React, { useState } from 'react';

const EconomicCalendar = () => {
  const [filterImportance, setFilterImportance] = useState('all');
  
  // Mock data for economic events
  const economicEvents = [
    {
      id: 'event-1',
      title: 'FOMC Meeting Minutes',
      date: '2025-05-05',
      time: '14:00',
      country: 'US',
      importance: 'high',
      previous: 'N/A',
      forecast: 'N/A',
      impact: 'Potentially significant for equity and bond markets. Focus on inflation outlook and rate cut signals.',
      related: ['SPY', 'TLT', 'UUP', 'GLD'],
      probability: {
        rateHold: 85,
        rateCut: 15,
        rateHike: 0
      }
    },
    {
      id: 'event-2',
      title: 'Non-Farm Payrolls',
      date: '2025-05-07',
      time: '08:30',
      country: 'US',
      importance: 'high',
      previous: '210K',
      forecast: '185K',
      impact: 'Key employment data that will influence Fed policy decisions. Weaker than expected could increase rate cut expectations.',
      related: ['SPY', 'QQQ', 'IWM', 'UUP'],
      probability: null
    },
    {
      id: 'event-3',
      title: 'ECB Interest Rate Decision',
      date: '2025-05-06',
      time: '07:45',
      country: 'EU',
      importance: 'high',
      previous: '3.75%',
      forecast: '3.75%',
      impact: 'Expected to hold rates, but market will focus on forward guidance and inflation outlook.',
      related: ['FEZ', 'EZU', 'HEDJ', 'EUR'],
      probability: {
        rateHold: 92,
        rateCut: 8,
        rateHike: 0
      }
    },
    {
      id: 'event-4',
      title: 'Retail Sales',
      date: '2025-05-08',
      time: '08:30',
      country: 'US',
      importance: 'medium',
      previous: '0.3%',
      forecast: '0.4%',
      impact: 'Key consumer spending indicator. Strong numbers would support economic growth narrative.',
      related: ['XLY', 'XRT', 'SPY'],
      probability: null
    },
    {
      id: 'event-5',
      title: 'CPI Data',
      date: '2025-05-12',
      time: '08:30',
      country: 'US',
      importance: 'high',
      previous: '3.2%',
      forecast: '3.0%',
      impact: 'Critical inflation reading that will heavily influence Fed policy path.',
      related: ['TIP', 'GLD', 'TLT', 'SPY'],
      probability: null
    },
    {
      id: 'event-6',
      title: 'GDP Growth Rate (Q1 Final)',
      date: '2025-05-15',
      time: '08:30',
      country: 'US',
      importance: 'medium',
      previous: '3.2%',
      forecast: '3.1%',
      impact: 'Final revision of Q1 economic growth. Major revisions could shift market sentiment.',
      related: ['SPY', 'DIA', 'IWM'],
      probability: null
    },
    {
      id: 'event-7',
      title: 'Bank of Japan Policy Statement',
      date: '2025-05-10',
      time: '03:00',
      country: 'JP',
      importance: 'medium',
      previous: '-0.1%',
      forecast: '-0.1%',
      impact: 'Focus on any signals of further policy normalization and yield curve control adjustments.',
      related: ['EWJ', 'YCS', 'JPY'],
      probability: {
        rateHold: 78,
        rateCut: 0,
        rateHike: 22
      }
    }
  ];

  // Filter events based on importance
  const filteredEvents = filterImportance === 'all' 
    ? economicEvents 
    : economicEvents.filter(event => event.importance === filterImportance);

  // Get country flag emoji
  const getCountryFlag = (country) => {
    switch (country) {
      case 'US':
        return '🇺🇸';
      case 'EU':
        return '🇪🇺';
      case 'UK':
        return '🇬🇧';
      case 'JP':
        return '🇯🇵';
      case 'CN':
        return '🇨🇳';
      case 'AU':
        return '🇦🇺';
      case 'CA':
        return '🇨🇦';
      default:
        return '';
    }
  };

  // Get importance badge color
  const getImportanceBadgeColor = (importance) => {
    switch (importance) {
      case 'high':
        return 'danger';
      case 'medium':
        return 'warning';
      case 'low':
        return 'info';
      default:
        return 'info';
    }
  };

  return (
    <div>
      <div className="dashboard-grid">
        <div className="card">
          <div className="card-header">
            <h2>Economic Calendar</h2>
            <select 
              value={filterImportance}
              onChange={(e) => setFilterImportance(e.target.value)}
              style={{ 
                backgroundColor: '#333', 
                color: 'white', 
                border: 'none', 
                padding: '5px 10px',
                borderRadius: '4px'
              }}
            >
              <option value="all">All Events</option>
              <option value="high">High Importance</option>
              <option value="medium">Medium Importance</option>
              <option value="low">Low Importance</option>
            </select>
          </div>
          
          <div className="card-content">
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Date/Time</th>
                    <th>Event</th>
                    <th>Country</th>
                    <th>Importance</th>
                    <th>Previous</th>
                    <th>Forecast</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredEvents.map((event) => (
                    <tr key={event.id}>
                      <td>
                        <div style={{ display: 'flex', flexDirection: 'column' }}>
                          <span style={{ fontWeight: 500 }}>{event.date}</span>
                          <span style={{ fontSize: '0.75rem', color: '#9e9e9e' }}>{event.time}</span>
                        </div>
                      </td>
                      <td>{event.title}</td>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                          <span style={{ fontSize: '1.2rem' }}>{getCountryFlag(event.country)}</span>
                          <span>{event.country}</span>
                        </div>
                      </td>
                      <td>
                        <span className={`badge ${getImportanceBadgeColor(event.importance)}`}>
                          {event.importance.charAt(0).toUpperCase() + event.importance.slice(1)}
                        </span>
                      </td>
                      <td>{event.previous}</td>
                      <td>{event.forecast}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
        
        <div className="card">
          <h2 className="card-header">Event Analysis</h2>
          <div className="card-content">
            <div style={{ 
              padding: '16px', 
              backgroundColor: '#272727', 
              borderRadius: '8px',
              marginBottom: '20px'
            }}>
              <h3 style={{ marginTop: 0, marginBottom: '12px' }}>FOMC Meeting Minutes</h3>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                <span style={{ fontSize: '1.2rem' }}>🇺🇸</span>
                <span>May 5, 2025 • 14:00</span>
                <span className="badge danger">High Importance</span>
              </div>
              
              <p style={{ margin: '0 0 16px 0', lineHeight: '1.5' }}>
                The Federal Open Market Committee (FOMC) will release minutes from its most recent meeting. Market participants will scrutinize the language for clues about the Fed's stance on inflation, economic growth, and potential rate cuts in coming months.
              </p>
              
              <div style={{ marginTop: '20px' }}>
                <h4 style={{ marginBottom: '12px' }}>Market Impact Analysis</h4>
                <p style={{ margin: '0 0 16px 0', lineHeight: '1.5' }}>
                  Potentially significant for equity and bond markets. Focus will be on inflation outlook and rate cut signals. Dovish language could boost equities, while hawkish comments might pressure growth stocks.
                </p>
                
                <h4 style={{ marginBottom: '12px' }}>AI Probability Analysis</h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                      <span>Rate Hold</span>
                      <span>85%</span>
                    </div>
                    <div className="progress-bar">
                      <div 
                        className="progress-bar-fill info" 
                        style={{ width: '85%' }}
                      />
                    </div>
                  </div>
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                      <span>Rate Cut</span>
                      <span>15%</span>
                    </div>
                    <div className="progress-bar">
                      <div 
                        className="progress-bar-fill success" 
                        style={{ width: '15%' }}
                      />
                    </div>
                  </div>
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                      <span>Rate Hike</span>
                      <span>0%</span>
                    </div>
                    <div className="progress-bar">
                      <div 
                        className="progress-bar-fill danger" 
                        style={{ width: '0%' }}
                      />
                    </div>
                  </div>
                </div>
                
                <h4 style={{ margin: '16px 0 12px 0' }}>Related Assets</h4>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                  <div className="badge info">SPY</div>
                  <div className="badge info">TLT</div>
                  <div className="badge info">UUP</div>
                  <div className="badge info">GLD</div>
                </div>
                
                <h4 style={{ margin: '16px 0 12px 0' }}>Trading Opportunities</h4>
                <div style={{ 
                  padding: '12px', 
                  backgroundColor: '#1e1e1e', 
                  borderRadius: '4px',
                  borderLeft: '3px solid #4F8BFF',
                  fontSize: '0.9rem',
                  lineHeight: '1.5'
                }}>
                  Consider volatility strategies around the event time. If minutes are more dovish than expected, growth stocks (QQQ) could outperform. Bond market (TLT) will likely be highly sensitive to language around inflation expectations and rate path.
                </div>
              </div>
            </div>
            
            <div style={{ textAlign: 'center' }}>
              <button
                style={{
                  backgroundColor: '#4F8BFF',
                  border: 'none',
                  padding: '8px 16px',
                  borderRadius: '4px',
                  color: 'white',
                  cursor: 'pointer',
                  marginRight: '12px'
                }}
              >
                Set Event Alerts
              </button>
              <button
                style={{
                  backgroundColor: 'transparent',
                  border: '1px solid #4F8BFF',
                  padding: '8px 16px',
                  borderRadius: '4px',
                  color: '#4F8BFF',
                  cursor: 'pointer'
                }}
              >
                Add to Calendar
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EconomicCalendar;
