import { useParams } from 'react-router-dom';

const DraftPage = () => {
  const { leagueId } = useParams<{ leagueId: string }>();

  return (
    <div className="max-w-6xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Draft Room</h1>
      <div className="bg-white rounded-lg shadow-md p-6">
        <p className="text-xl mb-4">League ID: {leagueId}</p>
        <p className="text-gray-600">
          This is a placeholder for the draft room UI that will be implemented in Story-14.
        </p>
      </div>
    </div>
  );
};

export default DraftPage;