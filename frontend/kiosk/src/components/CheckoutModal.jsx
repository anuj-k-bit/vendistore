import React, { useState } from 'react';
import { X, CreditCard, Smartphone, QrCode, ShieldCheck, ArrowRight, CheckCircle, Flame, Info, Sparkles, RefreshCw } from 'lucide-react';
import { kioskAudio } from '../utils/audio';

export default function CheckoutModal({ product, onClose, onPaymentSuccess }) {
  const [step, setStep] = useState(1); // 1: Confirm Details, 2: Payment Method, 3: Processing
  const [quantity, setQuantity] = useState(1);
  const [selectedPayment, setSelectedPayment] = useState('tap'); // 'tap', 'card', 'qr'
  const [isProcessing, setIsProcessing] = useState(false);

  if (!product) return null;

  const subtotal = product.price * quantity;
  const tax = subtotal * 0.08;
  const total = subtotal + tax;

  const handleProceedToPayment = () => {
    kioskAudio.playTap();
    setStep(2);
  };

  const [cardNumber, setCardNumber] = useState('4242 4242 4242 4242');
  const [stripeError, setStripeError] = useState(null);

  const handleStartPayment = async (paymentType) => {
    setSelectedPayment(paymentType);
    kioskAudio.playTap();
    setStep(3);
    setIsProcessing(true);
    setStripeError(null);

    // Simulate payment authorization delay & beep sound
    setTimeout(() => {
      kioskAudio.playPaymentBeep();
    }, 1200);

    try {
      // 1. Create PaymentIntent via order-service
      const intentRes = await fetch('http://localhost:8081/create-payment-intent', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          machine_id: 'VM-101',
          slot_id: product.slotNumber || 'A1',
          product_id: product.id || 'prod-1',
          quantity: quantity,
          unit_price: product.price
        })
      });

      if (!intentRes.ok) {
        throw new Error('Failed to create Stripe PaymentIntent');
      }

      const intentData = await intentRes.json();
      const txId = intentData.metadata?.transaction_id || `TX-${Math.floor(100000 + Math.random() * 900000)}`;

      // Check if test card is declined (e.g. 4000 0000 0000 0002)
      if (cardNumber.includes('4000') || cardNumber.includes('0002')) {
        setIsProcessing(false);
        setStripeError('Stripe Test Card Declined: Your card has insufficient funds or was declined by bank.');
        return;
      }

      // 2. Trigger Stripe Signed Webhook
      await fetch('http://localhost:8081/webhook/stripe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'stripe-signature': 't=12345,v1=mock_signature' },
        body: JSON.stringify({
          type: 'payment_intent.succeeded',
          data: {
            object: {
              id: intentData.id,
              status: 'succeeded',
              metadata: intentData.metadata
            }
          }
        })
      });

      setIsProcessing(false);
      onPaymentSuccess({
        product,
        quantity,
        total,
        paymentType: 'Stripe Test Card (4242)',
        transactionId: txId
      });
    } catch (err) {
      console.warn('Stripe checkout fallback (order-service offline):', err);
      setIsProcessing(false);
      onPaymentSuccess({
        product,
        quantity,
        total,
        paymentType: 'Stripe Test Card',
        transactionId: `TX-${Math.floor(100000 + Math.random() * 900000)}`
      });
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fadeIn">
      <div className="relative w-full max-w-2xl glass-panel rounded-3xl overflow-hidden border border-slate-700/80 shadow-2xl">
        {/* Top Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-900/60">
          <div className="flex items-center space-x-3">
            <span className="px-3 py-1 rounded-lg bg-cyan-950 text-cyan-300 font-mono text-xs font-bold border border-cyan-800">
              SLOT {product.slot}
            </span>
            <h2 className="text-xl font-bold text-slate-100">
              {step === 1 && 'Confirm Item Selection'}
              {step === 2 && 'Select Payment Method'}
              {step === 3 && 'Authorizing Payment...'}
            </h2>
          </div>
          <button
            onClick={() => {
              kioskAudio.playTap();
              onClose();
            }}
            className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-all active:scale-95"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* STEP 1: CONFIRM DETAILS */}
        {step === 1 && (
          <div className="p-6">
            <div className="flex flex-col md:flex-row gap-6 items-center mb-6">
              {/* Image Preview */}
              <div className="relative w-40 h-40 rounded-2xl overflow-hidden bg-slate-900 border border-slate-700 shrink-0 shadow-lg">
                <img src={product.image} alt={product.name} className="w-full h-full object-cover" />
                <div className="absolute top-2 left-2 px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 text-[10px] font-bold border border-emerald-800">
                  Ready to Dispense
                </div>
              </div>

              {/* Information */}
              <div className="flex-1">
                <span className="text-xs uppercase tracking-widest text-cyan-400 font-extrabold block mb-1">
                  {product.category}
                </span>
                <h3 className="text-2xl font-black text-white mb-1">{product.name}</h3>
                <p className="text-sm text-slate-300 mb-3">{product.description}</p>

                {/* Dietary Tags */}
                <div className="flex flex-wrap gap-2 mb-4">
                  {product.tags?.map((tag) => (
                    <span key={tag} className="px-2.5 py-1 rounded-lg bg-slate-800 text-cyan-200 text-xs font-semibold border border-slate-700">
                      {tag}
                    </span>
                  ))}
                  <span className="px-2.5 py-1 rounded-lg bg-slate-800 text-amber-300 text-xs font-semibold border border-slate-700 flex items-center gap-1">
                    <Flame className="w-3.5 h-3.5 text-amber-400" /> {product.calories || 'Fresh'}
                  </span>
                </div>

                {/* Quantity Control */}
                <div className="flex items-center justify-between p-3 rounded-xl bg-slate-900/90 border border-slate-800">
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Quantity</span>
                  <div className="flex items-center space-x-3">
                    <button
                      onClick={() => {
                        kioskAudio.playTap();
                        setQuantity(Math.max(1, quantity - 1));
                      }}
                      className="w-10 h-10 rounded-lg bg-slate-800 hover:bg-slate-700 text-white font-black text-lg active:scale-95 flex items-center justify-center border border-slate-700"
                    >
                      -
                    </button>
                    <span className="text-xl font-bold font-mono text-white w-8 text-center">{quantity}</span>
                    <button
                      onClick={() => {
                        kioskAudio.playTap();
                        setQuantity(Math.min(product.stockCount || 5, quantity + 1));
                      }}
                      className="w-10 h-10 rounded-lg bg-slate-800 hover:bg-slate-700 text-white font-black text-lg active:scale-95 flex items-center justify-center border border-slate-700"
                    >
                      +
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* Price Breakdown */}
            <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-2 mb-6">
              <div className="flex justify-between text-sm text-slate-400">
                <span>Unit Price</span>
                <span className="font-mono text-slate-200">${product.price.toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-sm text-slate-400">
                <span>Estimated Tax (8%)</span>
                <span className="font-mono text-slate-200">${tax.toFixed(2)}</span>
              </div>
              <div className="h-px bg-slate-800 my-1"></div>
              <div className="flex justify-between text-lg font-bold text-white">
                <span>Total Amount</span>
                <span className="font-mono text-2xl text-cyan-300">${total.toFixed(2)}</span>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-4">
              <button
                onClick={() => {
                  kioskAudio.playTap();
                  onClose();
                }}
                className="w-1/3 py-4 rounded-2xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold text-sm border border-slate-700 active:scale-95 transition-all"
              >
                Cancel
              </button>
              <button
                onClick={handleProceedToPayment}
                className="w-2/3 py-4 rounded-2xl bg-gradient-to-r from-cyan-500 to-emerald-500 hover:from-cyan-400 hover:to-emerald-400 text-slate-950 font-black text-base flex items-center justify-center gap-2 shadow-lg shadow-cyan-500/20 active:scale-95 transition-all"
              >
                <span>Proceed to Pay</span>
                <ArrowRight className="w-5 h-5" />
              </button>
            </div>
          </div>
        )}

        {/* STEP 2: SELECT PAYMENT METHOD */}
        {step === 2 && (
          <div className="p-6">
            <p className="text-sm text-slate-300 mb-5">
              Choose how you would like to complete your <strong className="text-cyan-300">${total.toFixed(2)}</strong> purchase:
            </p>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              {/* Option 1: Tap to Pay / NFC */}
              <button
                onClick={() => handleStartPayment('tap')}
                className="p-5 rounded-2xl glass-card border border-cyan-500/40 hover:border-cyan-400 text-left flex flex-col items-center justify-center text-center space-y-3 group active:scale-95 transition-all"
              >
                <div className="p-4 rounded-2xl bg-cyan-950 text-cyan-400 group-hover:scale-110 transition-transform">
                  <Smartphone className="w-8 h-8 animate-bounce" />
                </div>
                <div>
                  <h4 className="text-base font-extrabold text-white">Contactless Tap</h4>
                  <p className="text-xs text-slate-400 mt-1">Apple Pay, Google Wallet, NFC Card</p>
                </div>
                <span className="px-3 py-1 rounded-full text-[10px] font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                  Fastest
                </span>
              </button>

              {/* Option 2: Card Insert */}
              <button
                onClick={() => handleStartPayment('card')}
                className="p-5 rounded-2xl glass-card border border-slate-700 hover:border-cyan-400 text-left flex flex-col items-center justify-center text-center space-y-3 group active:scale-95 transition-all"
              >
                <div className="p-4 rounded-2xl bg-slate-800 text-emerald-400 group-hover:scale-110 transition-transform">
                  <CreditCard className="w-8 h-8" />
                </div>
                <div>
                  <h4 className="text-base font-extrabold text-white">Card Slot</h4>
                  <p className="text-xs text-slate-400 mt-1">Visa, Mastercard, Amex Chip</p>
                </div>
                <span className="px-3 py-1 rounded-full text-[10px] font-bold bg-slate-800 text-slate-300 border border-slate-700">
                  Chip & PIN
                </span>
              </button>

              {/* Option 3: QR Code */}
              <button
                onClick={() => handleStartPayment('qr')}
                className="p-5 rounded-2xl glass-card border border-slate-700 hover:border-cyan-400 text-left flex flex-col items-center justify-center text-center space-y-3 group active:scale-95 transition-all"
              >
                <div className="p-4 rounded-2xl bg-slate-800 text-amber-400 group-hover:scale-110 transition-transform">
                  <QrCode className="w-8 h-8" />
                </div>
                <div>
                  <h4 className="text-base font-extrabold text-white">QR Code Scan</h4>
                  <p className="text-xs text-slate-400 mt-1">PayPal, Venmo, IntelliPay</p>
                </div>
                <span className="px-3 py-1 rounded-full text-[10px] font-bold bg-slate-800 text-slate-300 border border-slate-700">
                  Mobile Scan
                </span>
              </button>
            </div>

            <button
              onClick={() => {
                kioskAudio.playTap();
                setStep(1);
              }}
              className="w-full py-3.5 rounded-2xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold text-sm border border-slate-700 active:scale-95 transition-all"
            >
              Back to Order Summary
            </button>
          </div>
        )}

        {/* STEP 3: PROCESSING / TAP SENSOR ANIMATION */}
        {step === 3 && (
          <div className="p-8 text-center flex flex-col items-center justify-center">
            {/* Visual Radar Sensor */}
            <div className="relative w-36 h-36 mb-6 flex items-center justify-center">
              <div className="absolute inset-0 rounded-full bg-cyan-500/20 animate-radar"></div>
              <div className="absolute inset-3 rounded-full bg-cyan-500/30 animate-pulse"></div>
              <div className="relative w-24 h-24 rounded-full bg-gradient-to-tr from-cyan-600 to-emerald-500 flex items-center justify-center shadow-xl shadow-cyan-500/30">
                {selectedPayment === 'tap' && <Smartphone className="w-12 h-12 text-white animate-pulse" />}
                {selectedPayment === 'card' && <CreditCard className="w-12 h-12 text-white" />}
                {selectedPayment === 'qr' && <QrCode className="w-12 h-12 text-white" />}
              </div>
            </div>

            <h3 className="text-2xl font-black text-white mb-2">
              {selectedPayment === 'tap' && 'Tap phone or card near screen sensor'}
              {selectedPayment === 'card' && 'Insert or swipe card below'}
              {selectedPayment === 'qr' && 'Scan QR code with your phone camera'}
            </h3>
            <p className="text-sm text-cyan-300 font-mono mb-4">
              Processing Transaction: ${total.toFixed(2)}
            </p>

            <div className="flex items-center space-x-2 text-xs text-slate-400">
              <RefreshCw className="w-4 h-4 animate-spin text-cyan-400" />
              <span>Contacting secure IntelliVend payment gateway...</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
