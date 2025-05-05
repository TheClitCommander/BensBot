# BensBot Pro Trading Dashboard

A professional-grade React dashboard for BensBot trading platform with modern UI, real-time monitoring, and strategy management.

## Features

- **Modern UI**: Dark-themed professional trading interface
- **Performance Visualization**: Interactive charts for portfolio performance
- **Strategy Pipeline**: Full strategy lifecycle from backtest to live trading
- **Signal Management**: Approve/reject trading signals with confidence metrics
- **Position Management**: Monitor and manage active positions
- **Advanced Analytics**: Strategy performance by market regime, feature importance

## Project Structure

```
bensbot-pro-dashboard/
├── app/
│   ├── api/              # API routes to connect to MongoDB
│   ├── dashboard/        # Dashboard routes
│   │   ├── overview/
│   │   ├── pipeline/
│   │   ├── signals/
│   │   ├── analytics/
│   │   ├── logs/
│   │   └── settings/
│   └── layout.tsx        # Main layout
├── components/           # UI components
│   ├── charts/           # Chart components
│   ├── dashboard/        # Dashboard-specific components 
│   ├── ui/               # UI components
│   └── layout/           # Layout components
├── lib/                  # Utility functions
├── public/               # Static assets
```

## Setup Instructions

1. Install dependencies:
   ```bash
   cd bensbot-pro-dashboard
   npm install
   ```

2. Create a `.env.local` file with your MongoDB connection details:
   ```
   MONGODB_URI=mongodb://localhost:27017
   ```

3. Run the development server:
   ```bash
   npm run dev
   ```

4. Open [http://localhost:3000](http://localhost:3000) in your browser

## MongoDB Integration

The dashboard connects to your existing BensBot MongoDB database to fetch:

- Portfolio data
- Strategy performance metrics
- Open positions
- Trading signals
- System logs
- Market context

## Next Steps

- Implement user authentication
- Add real-time data updates
- Create mobile-responsive views
- Set up notifications
- Add strategy back-testing form

## Technologies Used

- Next.js 13+ (App Router)
- React 18
- TypeScript
- Tailwind CSS
- Recharts
- MongoDB
- Lucide React (icons)
- SWR (data fetching)
