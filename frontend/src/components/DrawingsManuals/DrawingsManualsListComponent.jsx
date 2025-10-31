/**
 * Drawings & Manuals List Component
 * Wrapper component that receives selectedShip from parent
 */
import React from 'react';
import { DrawingsManualsTable } from './DrawingsManualsTable';

export const DrawingsManualsListComponent = ({ selectedShip }) => {
  return <DrawingsManualsTable selectedShip={selectedShip} />;
};
