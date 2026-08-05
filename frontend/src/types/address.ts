export interface Address {
  id: number;
  city: string;
  district: string;
  street: string;
  building: string;
}

export interface AddressPayload {
  city: string;
  district: string;
  street: string;
  building: string;
}

export interface AddressesResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: Address[];
}
