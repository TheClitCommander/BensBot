import TradeSignals from '@/components/dashboard/TradeSignals';
import OpenPositions from '@/components/dashboard/OpenPositions';

export default function SignalsPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Signals & Approvals</h1>
      
      <div className="grid grid-cols-1 gap-6">
        {/* Trade Signals & Approvals */}
        <TradeSignals />
        
        {/* Open Positions */}
        <OpenPositions />
      </div>
    </div>
  );
}
