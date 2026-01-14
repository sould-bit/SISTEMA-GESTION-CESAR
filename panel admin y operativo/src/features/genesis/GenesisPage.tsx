import { useAppSelector } from '../../stores/store';
import { GenesisLayout } from './GenesisLayout';
import { Step1Foundation } from './steps/Step1Foundation';
import { Step2Territory } from './steps/Step2Territory';
import { Step3Command } from './steps/Step3Command';

export const GenesisPage = () => {
    const currentStep = useAppSelector((state) => state.genesis.currentStep);

    const renderStep = () => {
        switch (currentStep) {
            case 1:
                return <Step1Foundation />;
            case 2:
                return <Step2Territory />;
            case 3:
                return <Step3Command />;
            default:
                return <Step1Foundation />;
        }
    };

    return (
        <GenesisLayout>
            {renderStep()}
        </GenesisLayout>
    );
};
