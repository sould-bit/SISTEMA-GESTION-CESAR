/**
 * RecipesPage - Wrapper for Recipe Builder
 */

import { ImprovedRecipeBuilder } from './ImprovedRecipeBuilder';
import { useNavigate } from 'react-router-dom';

export const RecipesPage = () => {
    const navigate = useNavigate();

    const handleSave = (recipe: any) => {
        console.log('Recipe saved:', recipe);
        // Could navigate to recipe list or show success
    };

    const handleCancel = () => {
        navigate('/kitchen/ingredients');
    };

    return (
        <div className="space-y-6">
            <ImprovedRecipeBuilder onSave={handleSave} onCancel={handleCancel} />
        </div>
    );
};

export default RecipesPage;
