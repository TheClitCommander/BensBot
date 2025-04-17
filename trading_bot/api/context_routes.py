from flask import Blueprint, jsonify, request, current_app
import logging
import json

context_bp = Blueprint('context', __name__)
logger = logging.getLogger(__name__)

@context_bp.route('/api/market-context', methods=['GET'])
def get_market_context():
    """Get current market sentiment and context"""
    try:
        # Get query parameters
        refresh = request.args.get('refresh', 'false').lower() == 'true'
        symbols = request.args.get('symbols')
        
        # Parse symbols if provided
        focus_symbols = None
        if symbols:
            focus_symbols = [s.strip().upper() for s in symbols.split(',')]
        
        # Get context analyzer
        context_analyzer = current_app.config['MARKET_CONTEXT_ANALYZER']
        
        # Get context
        context = context_analyzer.get_market_context(
            force_refresh=refresh,
            focus_symbols=focus_symbols
        )
        
        return jsonify({
            'status': 'success',
            'data': context
        })
    except Exception as e:
        logger.error(f"Error getting market context: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@context_bp.route('/api/strategy-recommendation', methods=['GET'])
def get_strategy_recommendation():
    """Get recommended trading strategies based on current market"""
    try:
        # Get query parameters
        symbols = request.args.get('symbols')
        
        # Parse symbols if provided
        focus_symbols = None
        if symbols:
            focus_symbols = [s.strip().upper() for s in symbols.split(',')]
        
        # Get context analyzer
        context_analyzer = current_app.config['MARKET_CONTEXT_ANALYZER']
        
        # Get context
        context = context_analyzer.get_market_context(focus_symbols=focus_symbols)
        
        # Extract strategies and reasoning
        strategies = context.get('suggested_strategies', [])
        triggers = context.get('triggers', [])
        reasoning = context.get('reasoning', '')
        
        return jsonify({
            'status': 'success',
            'data': {
                'market_bias': context.get('bias'),
                'confidence': context.get('confidence'),
                'recommended_strategies': strategies,
                'market_drivers': triggers,
                'analysis': reasoning,
                'timestamp': context.get('timestamp')
            }
        })
    except Exception as e:
        logger.error(f"Error getting strategy recommendations: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@context_bp.route('/api/context-scheduler/status', methods=['GET'])
def get_scheduler_status():
    """Get status of the adaptive context scheduler"""
    try:
        # Get scheduler from app config
        scheduler = current_app.config.get('CONTEXT_SCHEDULER')
        
        if not scheduler:
            return jsonify({
                'status': 'error',
                'message': 'Context scheduler not initialized'
            }), 404
        
        # Get scheduler status
        status = scheduler.get_status()
        
        return jsonify({
            'status': 'success',
            'data': status
        })
    except Exception as e:
        logger.error(f"Error getting scheduler status: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@context_bp.route('/api/context-scheduler/update', methods=['POST'])
def trigger_context_update():
    """Manually trigger a context update"""
    try:
        # Get scheduler from app config
        scheduler = current_app.config.get('CONTEXT_SCHEDULER')
        
        if not scheduler:
            return jsonify({
                'status': 'error',
                'message': 'Context scheduler not initialized'
            }), 404
        
        # Get parameter for daily update
        is_daily = request.args.get('daily', 'false').lower() == 'true'
        
        # Trigger update
        output_path = scheduler.update_market_context(is_daily_update=is_daily)
        
        if not output_path:
            return jsonify({
                'status': 'error',
                'message': 'Failed to update context'
            }), 500
        
        return jsonify({
            'status': 'success',
            'message': f'Context updated successfully',
            'output_path': output_path
        })
    except Exception as e:
        logger.error(f"Error triggering context update: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@context_bp.route('/api/context-scheduler/config', methods=['GET', 'POST'])
def scheduler_config():
    """Get or update scheduler configuration"""
    try:
        # Get scheduler from app config
        scheduler = current_app.config.get('CONTEXT_SCHEDULER')
        
        if not scheduler:
            return jsonify({
                'status': 'error',
                'message': 'Context scheduler not initialized'
            }), 404
        
        # Handle POST request to update config
        if request.method == 'POST':
            if not request.is_json:
                return jsonify({
                    'status': 'error',
                    'message': 'Request must be JSON'
                }), 400
            
            data = request.json
            
            # Update configurable parameters
            if 'market_hours_interval' in data:
                scheduler.market_hours_interval = int(data['market_hours_interval'])
            
            if 'after_hours_interval' in data:
                scheduler.after_hours_interval = int(data['after_hours_interval'])
            
            return jsonify({
                'status': 'success',
                'message': 'Configuration updated',
                'config': {
                    'market_hours_start': scheduler.market_hours_start,
                    'market_hours_end': scheduler.market_hours_end,
                    'market_hours_interval': scheduler.market_hours_interval,
                    'after_hours_interval': scheduler.after_hours_interval
                }
            })
        
        # Handle GET request to retrieve config
        return jsonify({
            'status': 'success',
            'config': {
                'market_hours_start': scheduler.market_hours_start,
                'market_hours_end': scheduler.market_hours_end,
                'market_hours_interval': scheduler.market_hours_interval,
                'after_hours_interval': scheduler.after_hours_interval,
                'is_market_hours': scheduler.is_market_hours()
            }
        })
    except Exception as e:
        logger.error(f"Error handling scheduler config: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500 