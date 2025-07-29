export * from './affiliateCreatorV202405Api';
import { AffiliateCreatorV202405Api, AffiliateCreatorV202405ApiOperationNames, AffiliateCreatorV202405ApiOperationTypes } from './affiliateCreatorV202405Api';
export * from './affiliateCreatorV202407Api';
import { AffiliateCreatorV202407Api, AffiliateCreatorV202407ApiOperationNames, AffiliateCreatorV202407ApiOperationTypes } from './affiliateCreatorV202407Api';
export * from './affiliateCreatorV202409Api';
import { AffiliateCreatorV202409Api, AffiliateCreatorV202409ApiOperationNames, AffiliateCreatorV202409ApiOperationTypes } from './affiliateCreatorV202409Api';
export * from './affiliateCreatorV202410Api';
import { AffiliateCreatorV202410Api, AffiliateCreatorV202410ApiOperationNames, AffiliateCreatorV202410ApiOperationTypes } from './affiliateCreatorV202410Api';
export * from './affiliateCreatorV202412Api';
import { AffiliateCreatorV202412Api, AffiliateCreatorV202412ApiOperationNames, AffiliateCreatorV202412ApiOperationTypes } from './affiliateCreatorV202412Api';
export * from './affiliateCreatorV202501Api';
import { AffiliateCreatorV202501Api, AffiliateCreatorV202501ApiOperationNames, AffiliateCreatorV202501ApiOperationTypes } from './affiliateCreatorV202501Api';
export * from './affiliatePartnerV202405Api';
import { AffiliatePartnerV202405Api, AffiliatePartnerV202405ApiOperationNames, AffiliatePartnerV202405ApiOperationTypes } from './affiliatePartnerV202405Api';
export * from './affiliatePartnerV202411Api';
import { AffiliatePartnerV202411Api, AffiliatePartnerV202411ApiOperationNames, AffiliatePartnerV202411ApiOperationTypes } from './affiliatePartnerV202411Api';
export * from './affiliatePartnerV202501Api';
import { AffiliatePartnerV202501Api, AffiliatePartnerV202501ApiOperationNames, AffiliatePartnerV202501ApiOperationTypes } from './affiliatePartnerV202501Api';
export * from './affiliatePartnerV202505Api';
import { AffiliatePartnerV202505Api, AffiliatePartnerV202505ApiOperationNames, AffiliatePartnerV202505ApiOperationTypes } from './affiliatePartnerV202505Api';
export * from './affiliateSellerV202405Api';
import { AffiliateSellerV202405Api, AffiliateSellerV202405ApiOperationNames, AffiliateSellerV202405ApiOperationTypes } from './affiliateSellerV202405Api';
export * from './affiliateSellerV202406Api';
import { AffiliateSellerV202406Api, AffiliateSellerV202406ApiOperationNames, AffiliateSellerV202406ApiOperationTypes } from './affiliateSellerV202406Api';
export * from './affiliateSellerV202409Api';
import { AffiliateSellerV202409Api, AffiliateSellerV202409ApiOperationNames, AffiliateSellerV202409ApiOperationTypes } from './affiliateSellerV202409Api';
export * from './affiliateSellerV202410Api';
import { AffiliateSellerV202410Api, AffiliateSellerV202410ApiOperationNames, AffiliateSellerV202410ApiOperationTypes } from './affiliateSellerV202410Api';
export * from './affiliateSellerV202412Api';
import { AffiliateSellerV202412Api, AffiliateSellerV202412ApiOperationNames, AffiliateSellerV202412ApiOperationTypes } from './affiliateSellerV202412Api';
export * from './affiliateSellerV202505Api';
import { AffiliateSellerV202505Api, AffiliateSellerV202505ApiOperationNames, AffiliateSellerV202505ApiOperationTypes } from './affiliateSellerV202505Api';
export * from './affiliateSellerV202507Api';
import { AffiliateSellerV202507Api, AffiliateSellerV202507ApiOperationNames, AffiliateSellerV202507ApiOperationTypes } from './affiliateSellerV202507Api';
export * from './affiliateV202309Api';
import { AffiliateV202309Api, AffiliateV202309ApiOperationNames, AffiliateV202309ApiOperationTypes } from './affiliateV202309Api';
export * from './affiliateV202402Api';
import { AffiliateV202402Api, AffiliateV202402ApiOperationNames, AffiliateV202402ApiOperationTypes } from './affiliateV202402Api';
export * from './affiliateV202403Api';
import { AffiliateV202403Api, AffiliateV202403ApiOperationNames, AffiliateV202403ApiOperationTypes } from './affiliateV202403Api';
export * from './authorizationV202309Api';
import { AuthorizationV202309Api, AuthorizationV202309ApiOperationNames, AuthorizationV202309ApiOperationTypes } from './authorizationV202309Api';
export * from './authorizationV202312Api';
import { AuthorizationV202312Api, AuthorizationV202312ApiOperationNames, AuthorizationV202312ApiOperationTypes } from './authorizationV202312Api';
export * from './authorizationV202401Api';
import { AuthorizationV202401Api, AuthorizationV202401ApiOperationNames, AuthorizationV202401ApiOperationTypes } from './authorizationV202401Api';
export * from './authorizationV202403Api';
import { AuthorizationV202403Api, AuthorizationV202403ApiOperationNames, AuthorizationV202403ApiOperationTypes } from './authorizationV202403Api';
export * from './authorizationV202405Api';
import { AuthorizationV202405Api, AuthorizationV202405ApiOperationNames, AuthorizationV202405ApiOperationTypes } from './authorizationV202405Api';
export * from './eventV202309Api';
import { EventV202309Api, EventV202309ApiOperationNames, EventV202309ApiOperationTypes } from './eventV202309Api';
import * as http from 'http';

export class HttpError extends Error {
constructor (public response: http.IncomingMessage, public body: any, public statusCode?: number) {
super('HTTP request failed');
this.name = 'HttpError';
}
}

export { RequestFile } from '../model/models';

export const APIS = [AffiliateCreatorV202405Api, AffiliateCreatorV202407Api, AffiliateCreatorV202409Api, AffiliateCreatorV202410Api, AffiliateCreatorV202412Api, AffiliateCreatorV202501Api, AffiliatePartnerV202405Api, AffiliatePartnerV202411Api, AffiliatePartnerV202501Api, AffiliatePartnerV202505Api, AffiliateSellerV202405Api, AffiliateSellerV202406Api, AffiliateSellerV202409Api, AffiliateSellerV202410Api, AffiliateSellerV202412Api, AffiliateSellerV202505Api, AffiliateSellerV202507Api, AffiliateV202309Api, AffiliateV202402Api, AffiliateV202403Api, AuthorizationV202309Api, AuthorizationV202312Api, AuthorizationV202401Api, AuthorizationV202403Api, AuthorizationV202405Api, EventV202309Api];

export enum API_ENUM {
    AffiliateCreatorV202405Api='AffiliateCreatorV202405Api', 
    AffiliateCreatorV202407Api='AffiliateCreatorV202407Api', 
    AffiliateCreatorV202409Api='AffiliateCreatorV202409Api', 
    AffiliateCreatorV202410Api='AffiliateCreatorV202410Api', 
    AffiliateCreatorV202412Api='AffiliateCreatorV202412Api', 
    AffiliateCreatorV202501Api='AffiliateCreatorV202501Api', 
    AffiliatePartnerV202405Api='AffiliatePartnerV202405Api', 
    AffiliatePartnerV202411Api='AffiliatePartnerV202411Api', 
    AffiliatePartnerV202501Api='AffiliatePartnerV202501Api', 
    AffiliatePartnerV202505Api='AffiliatePartnerV202505Api', 
    AffiliateSellerV202405Api='AffiliateSellerV202405Api', 
    AffiliateSellerV202406Api='AffiliateSellerV202406Api', 
    AffiliateSellerV202409Api='AffiliateSellerV202409Api', 
    AffiliateSellerV202410Api='AffiliateSellerV202410Api', 
    AffiliateSellerV202412Api='AffiliateSellerV202412Api', 
    AffiliateSellerV202505Api='AffiliateSellerV202505Api', 
    AffiliateSellerV202507Api='AffiliateSellerV202507Api', 
    AffiliateV202309Api='AffiliateV202309Api', 
    AffiliateV202402Api='AffiliateV202402Api', 
    AffiliateV202403Api='AffiliateV202403Api', 
    AuthorizationV202309Api='AuthorizationV202309Api', 
    AuthorizationV202312Api='AuthorizationV202312Api', 
    AuthorizationV202401Api='AuthorizationV202401Api', 
    AuthorizationV202403Api='AuthorizationV202403Api', 
    AuthorizationV202405Api='AuthorizationV202405Api', 
    EventV202309Api='EventV202309Api'
}

export const API_OBJECT = {
    AffiliateCreatorV202405Api:AffiliateCreatorV202405Api, 
    AffiliateCreatorV202407Api:AffiliateCreatorV202407Api, 
    AffiliateCreatorV202409Api:AffiliateCreatorV202409Api, 
    AffiliateCreatorV202410Api:AffiliateCreatorV202410Api, 
    AffiliateCreatorV202412Api:AffiliateCreatorV202412Api, 
    AffiliateCreatorV202501Api:AffiliateCreatorV202501Api, 
    AffiliatePartnerV202405Api:AffiliatePartnerV202405Api, 
    AffiliatePartnerV202411Api:AffiliatePartnerV202411Api, 
    AffiliatePartnerV202501Api:AffiliatePartnerV202501Api, 
    AffiliatePartnerV202505Api:AffiliatePartnerV202505Api, 
    AffiliateSellerV202405Api:AffiliateSellerV202405Api, 
    AffiliateSellerV202406Api:AffiliateSellerV202406Api, 
    AffiliateSellerV202409Api:AffiliateSellerV202409Api, 
    AffiliateSellerV202410Api:AffiliateSellerV202410Api, 
    AffiliateSellerV202412Api:AffiliateSellerV202412Api, 
    AffiliateSellerV202505Api:AffiliateSellerV202505Api, 
    AffiliateSellerV202507Api:AffiliateSellerV202507Api, 
    AffiliateV202309Api:AffiliateV202309Api, 
    AffiliateV202402Api:AffiliateV202402Api, 
    AffiliateV202403Api:AffiliateV202403Api, 
    AuthorizationV202309Api:AuthorizationV202309Api, 
    AuthorizationV202312Api:AuthorizationV202312Api, 
    AuthorizationV202401Api:AuthorizationV202401Api, 
    AuthorizationV202403Api:AuthorizationV202403Api, 
    AuthorizationV202405Api:AuthorizationV202405Api, 
    EventV202309Api:EventV202309Api
} as const;

export const API_OPERATION_NAME_MAP = {
    AffiliateCreatorV202405Api:AffiliateCreatorV202405ApiOperationNames, 
    AffiliateCreatorV202407Api:AffiliateCreatorV202407ApiOperationNames, 
    AffiliateCreatorV202409Api:AffiliateCreatorV202409ApiOperationNames, 
    AffiliateCreatorV202410Api:AffiliateCreatorV202410ApiOperationNames, 
    AffiliateCreatorV202412Api:AffiliateCreatorV202412ApiOperationNames, 
    AffiliateCreatorV202501Api:AffiliateCreatorV202501ApiOperationNames, 
    AffiliatePartnerV202405Api:AffiliatePartnerV202405ApiOperationNames, 
    AffiliatePartnerV202411Api:AffiliatePartnerV202411ApiOperationNames, 
    AffiliatePartnerV202501Api:AffiliatePartnerV202501ApiOperationNames, 
    AffiliatePartnerV202505Api:AffiliatePartnerV202505ApiOperationNames, 
    AffiliateSellerV202405Api:AffiliateSellerV202405ApiOperationNames, 
    AffiliateSellerV202406Api:AffiliateSellerV202406ApiOperationNames, 
    AffiliateSellerV202409Api:AffiliateSellerV202409ApiOperationNames, 
    AffiliateSellerV202410Api:AffiliateSellerV202410ApiOperationNames, 
    AffiliateSellerV202412Api:AffiliateSellerV202412ApiOperationNames, 
    AffiliateSellerV202505Api:AffiliateSellerV202505ApiOperationNames, 
    AffiliateSellerV202507Api:AffiliateSellerV202507ApiOperationNames, 
    AffiliateV202309Api:AffiliateV202309ApiOperationNames, 
    AffiliateV202402Api:AffiliateV202402ApiOperationNames, 
    AffiliateV202403Api:AffiliateV202403ApiOperationNames, 
    AuthorizationV202309Api:AuthorizationV202309ApiOperationNames, 
    AuthorizationV202312Api:AuthorizationV202312ApiOperationNames, 
    AuthorizationV202401Api:AuthorizationV202401ApiOperationNames, 
    AuthorizationV202403Api:AuthorizationV202403ApiOperationNames, 
    AuthorizationV202405Api:AuthorizationV202405ApiOperationNames, 
    EventV202309Api:EventV202309ApiOperationNames
} as const;

export type API_OPERATION_TYPE_MAP = {
    AffiliateCreatorV202405Api:AffiliateCreatorV202405ApiOperationTypes;
    AffiliateCreatorV202407Api:AffiliateCreatorV202407ApiOperationTypes;
    AffiliateCreatorV202409Api:AffiliateCreatorV202409ApiOperationTypes;
    AffiliateCreatorV202410Api:AffiliateCreatorV202410ApiOperationTypes;
    AffiliateCreatorV202412Api:AffiliateCreatorV202412ApiOperationTypes;
    AffiliateCreatorV202501Api:AffiliateCreatorV202501ApiOperationTypes;
    AffiliatePartnerV202405Api:AffiliatePartnerV202405ApiOperationTypes;
    AffiliatePartnerV202411Api:AffiliatePartnerV202411ApiOperationTypes;
    AffiliatePartnerV202501Api:AffiliatePartnerV202501ApiOperationTypes;
    AffiliatePartnerV202505Api:AffiliatePartnerV202505ApiOperationTypes;
    AffiliateSellerV202405Api:AffiliateSellerV202405ApiOperationTypes;
    AffiliateSellerV202406Api:AffiliateSellerV202406ApiOperationTypes;
    AffiliateSellerV202409Api:AffiliateSellerV202409ApiOperationTypes;
    AffiliateSellerV202410Api:AffiliateSellerV202410ApiOperationTypes;
    AffiliateSellerV202412Api:AffiliateSellerV202412ApiOperationTypes;
    AffiliateSellerV202505Api:AffiliateSellerV202505ApiOperationTypes;
    AffiliateSellerV202507Api:AffiliateSellerV202507ApiOperationTypes;
    AffiliateV202309Api:AffiliateV202309ApiOperationTypes;
    AffiliateV202402Api:AffiliateV202402ApiOperationTypes;
    AffiliateV202403Api:AffiliateV202403ApiOperationTypes;
    AuthorizationV202309Api:AuthorizationV202309ApiOperationTypes;
    AuthorizationV202312Api:AuthorizationV202312ApiOperationTypes;
    AuthorizationV202401Api:AuthorizationV202401ApiOperationTypes;
    AuthorizationV202403Api:AuthorizationV202403ApiOperationTypes;
    AuthorizationV202405Api:AuthorizationV202405ApiOperationTypes;
    EventV202309Api:EventV202309ApiOperationTypes;
};

