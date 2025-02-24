import fs from 'node:fs'
import * as yaml from 'js-yaml';

export interface AppConfigProps {
    isLogin: boolean;
    isApproval: boolean;
    isPurchase: boolean;
}

// Parse YAML file
interface Config {
    prod_or_dev: {
        prod: boolean;
        dev: boolean;
    };
    api_url: {
        dev: string;
        prod: string;
    };
    api_routes: {
        login: string;
        approval: string;
        purchase: string;
    };
}

/* Cache the configuration so only read once */
let cachedConfig: Config | null = null;
const loadConfig = (): Config => {
    if(!cachedConfig) {
        const fileContents = fs.readFileSync('./config.yaml', 'utf8');
        cachedConfig = yaml.load(fileContents) as Config;
    }
    return cachedConfig;
};

export const getApiURL = ({ isLogin, isApproval, isPurchase }: AppConfigProps): string => {
    const config = loadConfig();
    const hostname = window.location.hostname;
    
    // Replace placeholder with actual hostname
    const devApiURL = config.api_url.dev.replace('${HOSTNAME}', hostname);
    const prodApiURL = config.api_url.prod.replace('${HOSTNAME}', hostname);

    // PROD URLs
    const prodLoginURL = `${prodApiURL}${config.api_routes.login}`;
    const prodApprovalURL = `${prodApiURL}${config.api_routes.approval}`;
    const prodPurchaseURL = `${prodApiURL}${config.api_routes.purchase}`;

    // DEV URLs
    const devLoginURL = `${devApiURL}${config.api_routes.login}`;
    const devApprovalURL = `${devApiURL}${config.api_routes.approval}`;
    const devPurchaseURL = `${devApiURL}${config.api_routes.purchase}`;

    // PROD Conditionals
    if (isLogin && config.prod_or_dev.prod) {
        return prodLoginURL;
    } else if (isApproval && config.prod_or_dev.prod) {
        return prodApprovalURL;
    } else if (isPurchase && config.prod_or_dev.prod) {
        return prodPurchaseURL;
    }

    // DEV Conditionals
    if (isLogin && config.prod_or_dev.dev) {
        return devLoginURL;
    } else if (isApproval && config.prod_or_dev.dev) {
        return devApprovalURL;
    } else if (isPurchase && config.prod_or_dev.dev) {
        return devPurchaseURL;
    }

    // Default case if no condition matches
    throw new Error("No valid API URL found for the given configuration.");
};
