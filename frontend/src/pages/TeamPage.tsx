import { useParams } from 'react-router-dom';

const TeamPage = () => {
  const { teamId } = useParams<{ teamId: string }>();

  return (
    <div className="max-w-6xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Team Management</h1>
      <div className="bg-white rounded-lg shadow-md p-6">
        <p className="text-xl mb-4">Team ID: {teamId}</p>
        <p className="text-gray-600">
          This is a placeholder for the team management UI.
        </p>
      </div>
    </div>
  );
};

export default TeamPage;