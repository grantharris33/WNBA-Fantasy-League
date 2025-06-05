import React from 'react';
import { useNavigate } from 'react-router-dom';
import DashboardLayout from '../components/layout/DashboardLayout';

const HelpPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold leading-tight text-[#0d141c]">Help & Support</h1>
          <p className="text-slate-500 text-sm font-normal leading-normal mt-2">
            Get help with using the WNBA Fantasy League platform
          </p>
        </div>

        {/* Quick Start Guide */}
        <section className="mb-8">
          <div className="bg-white rounded-xl shadow-lg p-6 border border-slate-200">
            <h2 className="text-xl font-bold text-[#0d141c] mb-4">Quick Start Guide</h2>
            <div className="space-y-4">
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0 w-8 h-8 bg-[#0c7ff2] text-white rounded-full flex items-center justify-center text-sm font-bold">1</div>
                <div>
                  <h3 className="font-semibold text-slate-900">Join or Create a League</h3>
                  <p className="text-slate-600 text-sm">Start by joining an existing league or creating your own private league with friends.</p>
                </div>
              </div>
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0 w-8 h-8 bg-[#0c7ff2] text-white rounded-full flex items-center justify-center text-sm font-bold">2</div>
                <div>
                  <h3 className="font-semibold text-slate-900">Participate in the Draft</h3>
                  <p className="text-slate-600 text-sm">Draft your team of WNBA players in a live snake draft with your league members.</p>
                </div>
              </div>
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0 w-8 h-8 bg-[#0c7ff2] text-white rounded-full flex items-center justify-center text-sm font-bold">3</div>
                <div>
                  <h3 className="font-semibold text-slate-900">Manage Your Team</h3>
                  <p className="text-slate-600 text-sm">Set your starting lineup each week and make trades or waiver wire pickups.</p>
                </div>
              </div>
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0 w-8 h-8 bg-[#0c7ff2] text-white rounded-full flex items-center justify-center text-sm font-bold">4</div>
                <div>
                  <h3 className="font-semibold text-slate-900">Track Your Progress</h3>
                  <p className="text-slate-600 text-sm">Follow your team's performance and see how you stack up against other league members.</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Frequently Asked Questions */}
        <section className="mb-8">
          <div className="bg-white rounded-xl shadow-lg p-6 border border-slate-200">
            <h2 className="text-xl font-bold text-[#0d141c] mb-4">Frequently Asked Questions</h2>
            <div className="space-y-6">
              <div>
                <h3 className="font-semibold text-slate-900 mb-2">How does fantasy scoring work?</h3>
                <p className="text-slate-600 text-sm">
                  Players earn fantasy points based on their real-world WNBA performance. Points are awarded for statistics like points scored, rebounds, assists, steals, and blocks. Turnovers result in negative points.
                </p>
              </div>
              <div>
                <h3 className="font-semibold text-slate-900 mb-2">When do I need to set my lineup?</h3>
                <p className="text-slate-600 text-sm">
                  You can set your starting lineup at any time before the first game of the week begins. Make sure to check game schedules and set your lineup accordingly.
                </p>
              </div>
              <div>
                <h3 className="font-semibold text-slate-900 mb-2">How many moves can I make per week?</h3>
                <p className="text-slate-600 text-sm">
                  You can make up to 3 moves per week that affect your starting lineup. This includes trades, waiver wire pickups, and lineup changes. Bench moves don't count toward this limit.
                </p>
              </div>
              <div>
                <h3 className="font-semibold text-slate-900 mb-2">What are weekly bonuses?</h3>
                <p className="text-slate-600 text-sm">
                  Weekly bonuses are awarded to teams that achieve specific milestones, such as having the highest-scoring player of the week or reaching certain statistical thresholds.
                </p>
              </div>
              <div>
                <h3 className="font-semibold text-slate-900 mb-2">How do trades work?</h3>
                <p className="text-slate-600 text-sm">
                  You can propose trades with other league members. Both parties must accept the trade for it to be processed. Some leagues may have a review period for trades.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Game Rules */}
        <section className="mb-8">
          <div className="bg-white rounded-xl shadow-lg p-6 border border-slate-200">
            <h2 className="text-xl font-bold text-[#0d141c] mb-4">Game Rules</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="font-semibold text-slate-900 mb-3">Roster Requirements</h3>
                <ul className="space-y-2 text-sm text-slate-600">
                  <li>• Total roster size: 8-12 players</li>
                  <li>• Starting lineup: 5 players</li>
                  <li>• Bench players: 3-7 players</li>
                  <li>• Position requirements may apply</li>
                </ul>
              </div>
              <div>
                <h3 className="font-semibold text-slate-900 mb-3">Scoring System</h3>
                <ul className="space-y-2 text-sm text-slate-600">
                  <li>• Points: +1 point each</li>
                  <li>• Rebounds: +1 point each</li>
                  <li>• Assists: +1 point each</li>
                  <li>• Steals/Blocks: +1 point each</li>
                  <li>• Turnovers: -1 point each</li>
                </ul>
              </div>
              <div>
                <h3 className="font-semibold text-slate-900 mb-3">Weekly Moves</h3>
                <ul className="space-y-2 text-sm text-slate-600">
                  <li>• 3 starter moves per week maximum</li>
                  <li>• Unlimited bench transactions</li>
                  <li>• Moves reset every Monday</li>
                  <li>• Must be completed before games start</li>
                </ul>
              </div>
              <div>
                <h3 className="font-semibold text-slate-900 mb-3">Draft Rules</h3>
                <ul className="space-y-2 text-sm text-slate-600">
                  <li>• Snake draft format</li>
                  <li>• 90 seconds per pick</li>
                  <li>• Auto-pick if time expires</li>
                  <li>• Draft order randomized</li>
                </ul>
              </div>
            </div>
          </div>
        </section>

        {/* Contact Support */}
        <section>
          <div className="bg-white rounded-xl shadow-lg p-6 border border-slate-200">
            <h2 className="text-xl font-bold text-[#0d141c] mb-4">Need More Help?</h2>
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div>
                <p className="text-slate-600 text-sm mb-2">
                  Can't find what you're looking for? Our support team is here to help.
                </p>
                <p className="text-slate-500 text-xs">
                  We typically respond within 24 hours during business days.
                </p>
              </div>
              <div className="flex space-x-3">
                <button 
                  onClick={() => window.open('mailto:support@wnbafantasy.com', '_blank')}
                  className="px-4 py-2 bg-[#0c7ff2] text-white text-sm font-medium rounded-lg hover:bg-[#0a6bc8] transition-colors"
                >
                  Contact Support
                </button>
                <button 
                  onClick={() => navigate('/dashboard')}
                  className="px-4 py-2 border border-slate-300 text-slate-700 text-sm font-medium rounded-lg hover:bg-slate-50 transition-colors"
                >
                  Back to Dashboard
                </button>
              </div>
            </div>
          </div>
        </section>
      </div>
    </DashboardLayout>
  );
};

export default HelpPage;