# Trading Bot System

A sophisticated, containerized trading bot system with adaptive strategy rotation, continuous learning, and a modern dashboard UI.

## Overview

This trading bot system implements a dynamic strategy rotation mechanism that adapts to changing market conditions. The system combines traditional trading strategies (momentum, trend following, mean reversion) with reinforcement learning approaches to optimize trading performance.

## Key Features

- **Strategy Rotation**: Dynamically switches between trading strategies based on market regimes and performance
- **Market Regime Detection**: Identifies different market conditions (bull, bear, sideways, high/low volatility)
- **Continuous Learning**: Automatically retrains models based on performance feedback
- **Web Dashboard**: Modern UI for monitoring and controlling the system
- **Containerized Deployment**: Docker and Kubernetes support for scalable deployment

## System Architecture

The system is built with a microservices architecture and consists of the following components:

1. **Strategy Rotator**: Core component that manages different trading strategies and generates signals
2. **Continuous Learner**: Monitors strategy performance and retrains models as needed
3. **API Server**: FastAPI-based backend providing REST endpoints
4. **Web Dashboard**: React-based frontend for visualization and control
5. **Database**: PostgreSQL for persistent storage
6. **Cache**: Redis for high-speed data caching

## Containerization

The system is fully containerized using Docker, with orchestration available through Kubernetes or Docker Compose.

### Running with Docker Compose

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

### Kubernetes Deployment

Kubernetes configuration files are provided in the `kubernetes/` directory. To deploy to a Kubernetes cluster:

```bash
# Apply all configurations
kubectl apply -f kubernetes/

# Check deployment status
kubectl get pods

# Access the dashboard (port-forward)
kubectl port-forward svc/trading-bot-ui 3000:80
```

## Continuous Learning

The system implements a continuous learning pipeline that:

1. Monitors the performance of all trading strategies
2. Identifies underperforming strategies based on configurable thresholds
3. Automatically retrains models using recent market data
4. Updates the strategy weights based on performance

Configuration options for the continuous learning system are available in the ConfigMap or `config.yaml` file.

## User Interface

The dashboard provides the following views:

1. **Overview**: Key performance metrics, current market regime, and active strategies
2. **Strategies**: Detailed view of all strategies, with options to adjust weights or enable/disable
3. **Performance**: Historical performance metrics and charts
4. **Settings**: System configuration options

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Node.js 16+ (for local UI development)
- Python 3.9+ (for local backend development)

### Local Development

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/trading-bot.git
   cd trading-bot
   ```

2. Install backend dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Install frontend dependencies:
   ```bash
   cd ui
   npm install
   ```

4. Run the backend:
   ```bash
   python -m trading_bot.main
   ```

5. Run the frontend:
   ```bash
   cd ui
   npm start
   ```

### Configuration

The system can be configured through:

- Environment variables
- Configuration files in the `config/` directory
- Kubernetes ConfigMaps

## License

MIT License