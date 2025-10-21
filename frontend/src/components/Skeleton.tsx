import React from 'react';

interface SkeletonProps {
  className?: string;
}

/**
 * Basic Skeleton component for loading states
 */
export const Skeleton: React.FC<SkeletonProps> = ({ className = '' }) => {
  return (
    <div
      className={`animate-pulse bg-gray-200 dark:bg-gray-700 rounded ${className}`}
      aria-label="Loading..."
    />
  );
};

/**
 * Skeleton for a project card
 */
export const ProjectCardSkeleton: React.FC = () => {
  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6 shadow-sm">
      {/* Title */}
      <Skeleton className="h-6 w-3/4 mb-3" />
      
      {/* Description */}
      <Skeleton className="h-4 w-full mb-2" />
      <Skeleton className="h-4 w-5/6 mb-4" />
      
      {/* Status badge */}
      <Skeleton className="h-6 w-20 mb-4" />
      
      {/* Progress bar */}
      <Skeleton className="h-2 w-full mb-4" />
      
      {/* Metadata */}
      <div className="flex gap-4 mb-4">
        <Skeleton className="h-4 w-32" />
        <Skeleton className="h-4 w-32" />
      </div>
      
      {/* Buttons */}
      <div className="flex gap-2">
        <Skeleton className="h-10 w-32" />
        <Skeleton className="h-10 w-24" />
      </div>
    </div>
  );
};

/**
 * Skeleton for a list of project cards
 */
interface ProjectsGridSkeletonProps {
  count?: number;
}

export const ProjectsGridSkeleton: React.FC<ProjectsGridSkeletonProps> = ({ count = 6 }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {Array.from({ length: count }).map((_, index) => (
        <ProjectCardSkeleton key={index} />
      ))}
    </div>
  );
};

/**
 * Skeleton for table rows
 */
interface TableSkeletonProps {
  rows?: number;
  columns?: number;
}

export const TableSkeleton: React.FC<TableSkeletonProps> = ({ rows = 5, columns = 4 }) => {
  return (
    <div className="space-y-3">
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <div key={rowIndex} className="flex gap-4">
          {Array.from({ length: columns }).map((_, colIndex) => (
            <Skeleton
              key={colIndex}
              className="h-10 flex-1"
            />
          ))}
        </div>
      ))}
    </div>
  );
};

/**
 * Skeleton for a text block (e.g., article, documentation)
 */
interface TextSkeletonProps {
  lines?: number;
}

export const TextSkeleton: React.FC<TextSkeletonProps> = ({ lines = 5 }) => {
  return (
    <div className="space-y-3">
      {Array.from({ length: lines }).map((_, index) => (
        <Skeleton
          key={index}
          className={`h-4 ${index === lines - 1 ? 'w-2/3' : 'w-full'}`}
        />
      ))}
    </div>
  );
};

/**
 * Skeleton for a form
 */
export const FormSkeleton: React.FC = () => {
  return (
    <div className="space-y-6">
      {/* Form fields */}
      {Array.from({ length: 4 }).map((_, index) => (
        <div key={index}>
          <Skeleton className="h-5 w-32 mb-2" />
          <Skeleton className="h-10 w-full" />
        </div>
      ))}
      
      {/* Submit button */}
      <Skeleton className="h-12 w-40" />
    </div>
  );
};

export default Skeleton;
