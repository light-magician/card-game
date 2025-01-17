import React, { useState, useEffect, useRef } from 'react';
import { Move, ZoomIn, ZoomOut, Square, Group, MousePointer } from 'lucide-react';

const GameCanvas = () => {
  const [tool, setTool] = useState('pan'); // pan, draw, select
  const [selectedShapeIds, setSelectedShapeIds] = useState(new Set());
  const [zoom, setZoom] = useState(1);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const [shapes, setShapes] = useState([]);
  const [selectedShapes, setSelectedShapes] = useState([]);
  const [isDragging, setIsDragging] = useState(false);
  const [startPos, setStartPos] = useState({ x: 0, y: 0 });
  
  const canvasRef = useRef(null);
  const lastMousePos = useRef({ x: 0, y: 0 });

  // Convert screen coordinates to canvas coordinates
  const screenToCanvas = (x, y) => ({
    x: (x - offset.x) / zoom,
    y: (y - offset.y) / zoom
  });

  // Convert canvas coordinates to screen coordinates
  const canvasToScreen = (x, y) => ({
    x: x * zoom + offset.x,
    y: y * zoom + offset.y
  });

  // Helper to check if a point is inside a shape
  const isPointInShape = (x, y, shape) => {
    const screenPos = canvasToScreen(shape.x, shape.y);
    const width = shape.width * zoom;
    const height = shape.height * zoom;
    
    const shapeLeft = screenPos.x + Math.min(0, width);
    const shapeTop = screenPos.y + Math.min(0, height);
    const shapeRight = screenPos.x + Math.max(0, width);
    const shapeBottom = screenPos.y + Math.max(0, height);
    
    return x >= shapeLeft && x <= shapeRight && y >= shapeTop && y <= shapeBottom;
  };

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Backspace' || e.key === 'Delete') {
        if (selectedShapeIds.size > 0) {
          setShapes(shapes.filter(shape => !selectedShapeIds.has(shape.id)));
          setSelectedShapeIds(new Set());
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [shapes, selectedShapeIds]);

  const handleWheel = (e) => {
    // Only handle zoom if Control/Command is held
    if (e.ctrlKey || e.metaKey) {
      e.preventDefault();
      
      // Get mouse position relative to canvas
      const rect = canvasRef.current.getBoundingClientRect();
      const mouseX = e.clientX - rect.left;
      const mouseY = e.clientY - rect.top;

      // Convert mouse position to canvas coordinates before zoom
      const beforeZoomX = (mouseX - offset.x) / zoom;
      const beforeZoomY = (mouseY - offset.y) / zoom;

      // Calculate new zoom level
      const zoomFactor = e.deltaY > 0 ? 0.95 : 1.05;
      const newZoom = Math.max(0.1, Math.min(5, zoom * zoomFactor));
      
      // Convert same canvas position back to screen coordinates after zoom
      const afterZoomX = beforeZoomX * newZoom;
      const afterZoomY = beforeZoomY * newZoom;

      // Adjust offset to keep mouse position fixed
      setOffset({
        x: offset.x - (afterZoomX - (mouseX - offset.x)),
        y: offset.y - (afterZoomY - (mouseY - offset.y))
      });
      
      setZoom(newZoom);
    }
  };

  const handleMouseDown = (e) => {
    const rect = canvasRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    // Check if clicking on a resize handle
    if (tool === 'select' && selectedShapeIds.size === 1) {
      const selectedShape = shapes.find(shape => selectedShapeIds.has(shape.id));
      if (selectedShape) {
        const screenPos = canvasToScreen(selectedShape.x, selectedShape.y);
        const width = selectedShape.width * zoom;
        const height = selectedShape.height * zoom;
        
        const handleSize = 8;
        const handleHitbox = 12; // Slightly larger than visual size for easier grabbing
        
        // Store the original dimensions for resize calculations
        setResizeStartDims({
          x: selectedShape.x,
          y: selectedShape.y,
          width: selectedShape.width,
          height: selectedShape.height
        });

        // Check each resize handle
        // Left handle
        if (Math.abs(x - screenPos.x) < handleHitbox &&
            y > screenPos.y + height * 0.25 &&
            y < screenPos.y + height * 0.75) {
          setResizeHandle('left');
          setIsDragging(true);
          lastMousePos.current = { x, y };
          return;
        }
        
        // Right handle
        if (Math.abs(x - (screenPos.x + width)) < handleHitbox &&
            y > screenPos.y + height * 0.25 &&
            y < screenPos.y + height * 0.75) {
          setResizeHandle('right');
          setIsDragging(true);
          lastMousePos.current = { x, y };
          return;
        }
        
        // Top handle
        if (Math.abs(y - screenPos.y) < handleHitbox &&
            x > screenPos.x + width * 0.25 &&
            x < screenPos.x + width * 0.75) {
          setResizeHandle('top');
          setIsDragging(true);
          lastMousePos.current = { x, y };
          return;
        }
        
        // Bottom handle
        if (Math.abs(y - (screenPos.y + height)) < handleHitbox &&
            x > screenPos.x + width * 0.25 &&
            x < screenPos.x + width * 0.75) {
          setResizeHandle('bottom');
          setIsDragging(true);
          lastMousePos.current = { x, y };
          return;
        }
      }
    }
    const rect = canvasRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    setIsDragging(true);
    setStartPos({ x, y });
    lastMousePos.current = { x, y };

    if (tool === 'select') {
      const clickedShape = shapes.find(shape => isPointInShape(x, y, shape));
      
      if (clickedShape) {
        if (e.metaKey || e.ctrlKey) {  // Check for both Meta (Command) and Control keys
          // Toggle selection with Command/Control key
          setSelectedShapeIds(prev => {
            const newSelection = new Set(prev);
            if (newSelection.has(clickedShape.id)) {
              newSelection.delete(clickedShape.id);
            } else {
              newSelection.add(clickedShape.id);
            }
            return newSelection;
          });
        } else {
          // If clicking on an already selected shape, keep the current selection for dragging
          // Otherwise, select only this shape
          if (!selectedShapeIds.has(clickedShape.id)) {
            setSelectedShapeIds(new Set([clickedShape.id]));
          }
        }
      } else if (!(e.metaKey || e.ctrlKey)) {  // Clear selection only if neither Command nor Control is pressed
        // Clear selection when clicking empty space without Command/Control key
        setSelectedShapeIds(new Set());
      }
    } else if (tool === 'draw') {
      const canvasPos = screenToCanvas(x, y);
      const newShape = {
        id: Date.now(),
        type: 'rectangle',
        x: canvasPos.x,
        y: canvasPos.y,
        width: 0,
        height: 0
      };
      setShapes([...shapes, newShape]);
    }
  };

  const [resizeHandle, setResizeHandle] = useState(null); // null, 'left', 'right', 'top', 'bottom'
  const [resizeStartDims, setResizeStartDims] = useState(null);

  const handleMouseMove = (e) => {
    if (!isDragging) return;

    const rect = canvasRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    if (resizeHandle && selectedShapeIds.size === 1) {
      // Get the selected shape
      const selectedShape = shapes.find(shape => selectedShapeIds.has(shape.id));
      if (!selectedShape) return;

      const dx = (x - lastMousePos.current.x) / zoom;
      const dy = (y - lastMousePos.current.y) / zoom;

      setShapes(shapes.map(shape => {
        if (shape.id === selectedShape.id) {
          const newShape = { ...shape };
          
          if (resizeHandle === 'left') {
            newShape.x = resizeStartDims.x + dx;
            newShape.width = resizeStartDims.width - dx;
          } else if (resizeHandle === 'right') {
            newShape.width = resizeStartDims.width + dx;
          } else if (resizeHandle === 'top') {
            newShape.y = resizeStartDims.y + dy;
            newShape.height = resizeStartDims.height - dy;
          } else if (resizeHandle === 'bottom') {
            newShape.height = resizeStartDims.height + dy;
          }
          
          return newShape;
        }
        return shape;
      }));
    } else if (tool === 'select' && selectedShapeIds.size > 0) {
      const dx = (x - lastMousePos.current.x) / zoom;
      const dy = (y - lastMousePos.current.y) / zoom;
      
      setShapes(shapes.map(shape => {
        if (selectedShapeIds.has(shape.id)) {
          return {
            ...shape,
            x: shape.x + dx,
            y: shape.y + dy
          };
        }
        return shape;
      }));
    } else if (tool === 'pan') {
      const dx = x - lastMousePos.current.x;
      const dy = y - lastMousePos.current.y;
      setOffset({
        x: offset.x + dx,
        y: offset.y + dy
      });
    } else if (tool === 'draw') {
      const startCanvasPos = screenToCanvas(startPos.x, startPos.y);
      const currentCanvasPos = screenToCanvas(x, y);
      
      setShapes(shapes.map((shape, index) => {
        if (index === shapes.length - 1) {
          return {
            ...shape,
            width: currentCanvasPos.x - startCanvasPos.x,
            height: currentCanvasPos.y - startCanvasPos.y
          };
        }
        return shape;
      }));
    }
    
    lastMousePos.current = { x, y };
  };

  const handleMouseUp = () => {
    setIsDragging(false);
    setResizeHandle(null);
    setResizeStartDims(null);
  };

  const handleZoom = (factor) => {
    setZoom(Math.max(0.1, Math.min(5, zoom * factor)));
  };

  // Render shapes
  const renderShapes = () => {
    return shapes.map(shape => {
      if (shape.type === 'rectangle') {
        const screenPos = canvasToScreen(shape.x, shape.y);
        const width = shape.width * zoom;
        const height = shape.height * zoom;
        
        return (
          <div
            key={shape.id}
            className={`absolute border-2 ${
            selectedShapeIds.has(shape.id) 
              ? 'border-4 border-blue-600 bg-blue-100 bg-opacity-20' 
              : 'border-blue-500'
          }`}
            style={{
              left: screenPos.x,
              top: screenPos.y,
              width: Math.abs(width),
              height: Math.abs(height),
              transform: `translate(${width < 0 ? width : 0}px, ${height < 0 ? height : 0}px)`
            }}
          />
        );
      }
      return null;
    });
  };

  return (
    <div className="w-full h-screen flex">
      {/* Toolbar */}
      <div className="w-16 bg-gray-100 p-2 flex flex-col gap-2">
        <button
          className={`p-2 rounded ${tool === 'pan' ? 'bg-blue-200' : 'hover:bg-gray-200'}`}
          onClick={() => setTool('pan')}
        >
          <Move className="w-6 h-6" />
        </button>
        <button
          className={`p-2 rounded ${tool === 'draw' ? 'bg-blue-200' : 'hover:bg-gray-200'}`}
          onClick={() => setTool('draw')}
        >
          <Square className="w-6 h-6" />
        </button>
        <button
          className={`p-2 rounded ${tool === 'select' ? 'bg-blue-200' : 'hover:bg-gray-200'}`}
          onClick={() => setTool('select')}
        >
          <MousePointer className="w-6 h-6" />
        </button>
        <button
          className="p-2 rounded hover:bg-gray-200"
          onClick={() => handleZoom(1.2)}
        >
          <ZoomIn className="w-6 h-6" />
        </button>
        <button
          className="p-2 rounded hover:bg-gray-200"
          onClick={() => handleZoom(0.8)}
        >
          <ZoomOut className="w-6 h-6" />
        </button>
      </div>

      {/* Canvas */}
      <div
        ref={canvasRef}
        className={`flex-1 relative bg-white overflow-hidden ${
        tool === 'pan' 
          ? 'cursor-grab' 
          : tool === 'select' 
            ? selectedShapeIds.size > 0 ? 'cursor-move' : 'cursor-default'
            : tool === 'draw' 
              ? 'cursor-crosshair'
              : 'cursor-default'
      }`}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onWheel={handleWheel}
      >
        {renderShapes()}
      </div>
    </div>
  );
};

export default GameCanvas;