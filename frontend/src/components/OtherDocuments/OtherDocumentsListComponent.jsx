/**
 * Other Documents List Component
 * Wrapper component that renders the OtherDocumentsTable
 */
import React from 'react';
import OtherDocumentsTable from './OtherDocumentsTable';

export const OtherDocumentsListComponent = ({ selectedShip }) => {
  return <OtherDocumentsTable selectedShip={selectedShip} />;
};
