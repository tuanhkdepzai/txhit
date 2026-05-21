import math
import time
import requests
import os
import threading
from flask import Flask, jsonify

app = Flask(__name__)

class UltraDicePredictionSystem:
    def __init__(self):
        self.history = []
        self.models = {}
        self.weights = {}
        self.performance = {}
        self.pattern_database = {}
        self.advanced_patterns = {}
        
        self.session_stats = {
            'streaks': {'T': 0, 'X': 0, 'maxT': 0, 'maxX': 0},
            'transitions': {'TtoT': 0, 'TtoX': 0, 'XtoT': 0, 'XtoX': 0},
            'volatility': 0.5,
            'pattern_confidence': {},
            'recent_accuracy': 0,
            'bias': {'T': 0, 'X': 0}
        }
        
        self.market_state = {
            'trend': 'neutral',
            'momentum': 0,
            'stability': 0.5,
            'regime': 'normal' # normal, volatile, trending, random
        }
        
        self.adaptive_parameters = {
            'pattern_min_length': 3,
            'pattern_max_length': 8,
            'volatility_threshold': 0.7,
            'trend_strength_threshold': 0.6,
            'pattern_confidence_decay': 0.95,
            'pattern_confidence_growth': 1.05
        }
        
        self.init_all_models()

    def init_all_models(self):
        for i in range(1, 22):
            model_name = f"model{i}"
            self.weights[model_name] = 1.0
            self.performance[model_name] = {
                'correct': 0,
                'total': 0,
                'recent_correct': 0,
                'recent_total': 0,
                'streak': 0,
                'max_streak': 0
            }
            
        self.init_pattern_database()
        self.init_advanced_patterns()

    def init_pattern_database(self):
        self.pattern_database = {
            '1-1': {'pattern': ['T', 'X', 'T', 'X'], 'probability': 0.7, 'strength': 0.8},
            '1-2-1': {'pattern': ['T', 'X', 'X', 'T'], 'probability': 0.65, 'strength': 0.75},
            '2-1-2': {'pattern': ['T', 'T', 'X', 'T', 'T'], 'probability': 0.68, 'strength': 0.78},
            '3-1': {'pattern': ['T', 'T', 'T', 'X'], 'probability': 0.72, 'strength': 0.82},
            '1-3': {'pattern': ['T', 'X', 'X', 'X'], 'probability': 0.72, 'strength': 0.82},
            '2-2': {'pattern': ['T', 'T', 'X', 'X'], 'probability': 0.66, 'strength': 0.76},
            '2-3': {'pattern': ['T', 'T', 'X', 'X', 'X'], 'probability': 0.71, 'strength': 0.81},
            '3-2': {'pattern': ['T', 'T', 'T', 'X', 'X'], 'probability': 0.73, 'strength': 0.83},
            '4-1': {'pattern': ['T', 'T', 'T', 'T', 'X'], 'probability': 0.76, 'strength': 0.86},
            '1-4': {'pattern': ['T', 'X', 'X', 'X', 'X'], 'probability': 0.76, 'strength': 0.86},
        }

    def init_advanced_patterns(self):
        # 1. Các mẫu nâng cao động gốc
        self.advanced_patterns['dynamic-1'] = {
            'detect': lambda data: len(data) >= 6 and data[-6:].count('T') == 4 and data[-1] == 'T',
            'predict': lambda data: 'X',
            'confidence': 0.72,
            'description': "4T trong 6 phiên, cuối là T -> dự đoán X"
        }
        self.advanced_patterns['dynamic-2'] = {
            'detect': lambda data: len(data) >= 8 and data[-8:].count('T') >= 6 and data[-1] == 'T',
            'predict': lambda data: 'X',
            'confidence': 0.78,
            'description': "6+T trong 8 phiên, cuối là T -> dự đoán X mạnh"
        }
        self.advanced_patterns['alternating-3'] = {
            'detect': lambda data: len(data) >= 5 and all(data[-5:][i] != data[-5:][i-1] for i in range(1, 5)),
            'predict': lambda data: 'X' if data[-1] == 'T' else 'T',
            'confidence': 0.68,
            'description': "5 phiên đan xen hoàn hảo -> dự đoán đảo chiều"
        }
        self.advanced_patterns['cyclic-7'] = {
            'detect': lambda data: len(data) >= 14 and data[-14:-7] == data[-7:],
            'predict': lambda data: data[-7],
            'confidence': 0.75,
            'description': "Chu kỳ 7 phiên lặp lại -> dự đoán theo chu kỳ"
        }
        self.advanced_patterns['momentum-break'] = {
            'detect': lambda data: len(data) >= 9 and abs(data[-9:-3].count('T') - data[-9:-3].count('X')) >= 4 and len(set(data[-3:])) == 1 and data[-3] != ('T' if data[-9:-3].count('T') > data[-9:-3].count('X') else 'X'),
            'predict': lambda data: 'T' if data[-9:-3].count('T') > data[-9:-3].count('X') else 'X',
            'confidence': 0.71,
            'description': "Momentum mạnh bị phá vỡ -> quay lại xu hướng chính"
        }
        self.advanced_patterns['hybrid-pattern'] = {
            'detect': lambda data: len(data) >= 10 and 3 <= data[-10:].count('T') <= 7 and sum(1 for i in range(1, 10) if data[-10:][i] != data[-10:][i-1]) >= 6,
            'predict': lambda data: ('X' if data[-1] == 'T' else 'T') if data[-1] == data[-2] else data[-1],
            'confidence': 0.65,
            'description': "Hỗn hợp cao -> dự đoán theo lượt chuyển đổi"
        }

        # 2. Tích hợp Full Pattern từ danh sách thuật toán tĩnh
        raw_patterns = {'TXXTTXTX': 'Xỉu', 'XXTTXTXX': 'Tài', 'XTTXTXXT': 'Tài', 'TTXTXXTT': 'Tài', 'TXTXXTTT': 'Xỉu', 'XTXXTTTX': 'Xỉu', 'TXXTTTXX': 'Tài', 'XXTTTXXT': 'Xỉu', 'XTTTXXTX': 'Xỉu', 'TTTXXTXX': 'Xỉu', 'TTXXTXXX': 'Xỉu', 'TXXTXXXX': 'Xỉu', 'XXTXXXXX': 'Tài', 'XTXXXXXT': 'Xỉu', 'TXXXXXTX': 'Xỉu', 'XXXXXTXX': 'Xỉu', 'XXXXTXXX': 'Tài', 'XXXTXXXT': 'Xỉu', 'XXTXXXTX': 'Xỉu', 'XTXXXTXX': 'Xỉu', 'TXXXTXXX': 'Tài', 'XXXTXXXX': 'Tài', 'XXTXXXXT': 'Tài', 'XTXXXXTT': 'Tài', 'TXXXXTTX': 'Xỉu', 'XXXXTTXX': 'Xỉu', 'XXXTTXXX': 'Xỉu', 'XXTTXXXT': 'Xỉu', 'XTTXXXTX': 'Tài', 'TTXXXTXT': 'Xỉu', 'TXXXTXTX': 'Tài', 'XXXTTXTX': 'Xỉu', 'XXTXTXTT': 'Tài', 'XTXTXTTT': 'Tài', 'TXTXTTTT': 'Tài', 'XTXTTTTT': 'Tài', 'TXTTTTTT': 'Xỉu', 'XTTTTTTX': 'Tài', 'TTTTTTXT': 'Xỉu', 'TTTTTXTX': 'Tài', 'TTTTXTXT': 'Xỉu', 'TTTXTXTT': 'Xỉu', 'TTXTXTTX': 'Tài', 'TXTXTTXT': 'Xỉu', 'XTXTTXTX': 'Tài', 'TXTTXTXT': 'Tài', 'XTTXTXTT': 'Xỉu', 'TXTTXTXX': 'Xỉu', 'XTTXTXXX': 'Tài', 'TTXTXXXT': 'Tài', 'TXTXXXTT': 'Xỉu', 'XTXXXTTX': 'Xỉu', 'TXXXTTXX': 'Tài', 'XXXTTXXT': 'Xỉu', 'XXTTXXTX': 'Xỉu', 'XTTXXTXX': 'Xỉu', 'TXXTXXXT': 'Tài', 'XXTXXXTT': 'Tài', 'XTXXXTTT': 'Tài', 'TXXXTTTT': 'Tài', 'XXXTTTTT': 'Tài', 'XXTTTTTT': 'Xỉu', 'TTTTTTXX': 'Xỉu', 'TTTTTXXX': 'Tài', 'TTTTXXXT': 'Xỉu', 'TTTXXXTX': 'Tài', 'TTXXXTXX': 'Tài', 'TXXXTXXT': 'Xỉu', 'XXXTXXTX': 'Xỉu', 'XXTXXTXT': 'Xỉu', 'XXTTXXXX': 'Tài', 'XTTXXXXT': 'Xỉu', 'TTXXXXTX': 'Xỉu', 'TXXXXTXX': 'Tài', 'XXXXTXXT': 'Xỉu', 'XXTXXTXX': 'Xỉu', 'XTXXTXXX': 'Xỉu', 'XTXXXXXX': 'Xỉu', 'TXXXXXXX': 'Xỉu', 'XXXXXXXX': 'Tài', 'XXXXXXXT': 'Xỉu', 'XXXXXXTX': 'Xỉu', 'XXTTTTXT': 'Xỉu', 'XTTTTXTX': 'Tài', 'TTTXTXTX': 'Xỉu', 'TTXTXTXX': 'Xỉu', 'TXTXTXXX': 'Xỉu', 'XTXTXXXX': 'Tài', 'TXTXXXXT': 'Tài'}

        for i, (pattern_str, target_val) in enumerate(raw_patterns.items()):
            pattern_list = list(pattern_str)
            predict_char = 'T' if target_val == "Tài" else 'X'
            pattern_len = len(pattern_list)
            
            def make_detect_func(p_list, p_len):
                return lambda data: len(data) >= p_len and data[-p_len:] == p_list

            def make_predict_func(p_char):
                return lambda data: p_char

            self.advanced_patterns[f"static-logic-{i+1}"] = {
                'detect': make_detect_func(pattern_list, pattern_len),
                'predict': make_predict_func(predict_char),
                'confidence': 0.85,
                'description': f"Khớp chuỗi thuật toán cố định {pattern_str} -> Đặt {target_val}"
            }

    def add_result(self, result):
        if len(self.history) > 0:
            last_result = self.history[-1]
            transition_key = f"{last_result}to{result}"
            self.session_stats['transitions'][transition_key] = self.session_stats['transitions'].get(transition_key, 0) + 1
            
            if result == last_result:
                self.session_stats['streaks'][result] += 1
                self.session_stats['streaks'][f"max{result}"] = max(self.session_stats['streaks'][f"max{result}"], self.session_stats['streaks'][result])
            else:
                self.session_stats['streaks'][result] = 1
                self.session_stats['streaks'][last_result] = 0
        else:
            self.session_stats['streaks'][result] = 1
            
        self.history.append(result)
        if len(self.history) > 200:
            self.history.pop(0)
            
        self.update_volatility()
        self.update_pattern_confidence(result)
        self.update_market_state()
        self.update_pattern_database()

    def update_volatility(self):
        if len(self.history) < 10:
            return
        recent = self.history[-10:]
        changes = sum(1 for i in range(1, len(recent)) if recent[i] != recent[i-1])
        self.session_stats['volatility'] = changes / (len(recent) - 1)

    def update_pattern_confidence(self, last_result):
        if len(self.history) < 2:
            return
        history_before = self.history[:-1]
        for pattern_name, confidence in list(self.session_stats['pattern_confidence'].items()):
            if pattern_name in self.advanced_patterns:
                prediction = self.advanced_patterns[pattern_name]['predict'](history_before)
                if prediction != last_result:
                    self.session_stats['pattern_confidence'][pattern_name] = max(0.1, confidence * self.adaptive_parameters['pattern_confidence_decay'])
                else:
                    self.session_stats['pattern_confidence'][pattern_name] = min(0.95, confidence * self.adaptive_parameters['pattern_confidence_growth'])

    def update_market_state(self):
        if len(self.history) < 15:
            return
        recent = self.history[-15:]
        t_count = recent.count('T')
        x_count = recent.count('X')
        trend_strength = abs(t_count - x_count) / len(recent)
        
        if trend_strength > self.adaptive_parameters['trend_strength_threshold']:
            self.market_state['trend'] = 'up' if t_count > x_count else 'down'
        else:
            self.market_state['trend'] = 'neutral'
            
        momentum = 0.0
        for i in range(1, len(recent)):
            if recent[i] == recent[i-1]:
                momentum += 0.1 if recent[i] == 'T' else -0.1
        self.market_state['momentum'] = math.tanh(momentum)
        self.market_state['stability'] = 1 - self.session_stats['volatility']
        
        if self.session_stats['volatility'] > self.adaptive_parameters['volatility_threshold']:
            self.market_state['regime'] = 'volatile'
        elif trend_strength > 0.7:
            self.market_state['regime'] = 'trending'
        elif trend_strength < 0.3:
            self.market_state['regime'] = 'random'
        else:
            self.market_state['regime'] = 'normal'

    def update_pattern_database(self):
        if len(self.history) < 10:
            return
        min_l = self.adaptive_parameters['pattern_min_length']
        max_l = self.adaptive_parameters['pattern_max_length']
        for length in range(min_l, max_l + 1):
            for i in range(len(self.history) - length + 1):
                segment = self.history[i:i+length]
                pattern_key = "-".join(segment)
                if pattern_key not in self.pattern_database:
                    count = 0
                    for j in range(len(self.history) - length):
                        if self.history[j:j+length] == segment:
                            count += 1
                    if count > 2:
                        probability = count / (len(self.history) - length)
                        strength = min(0.9, probability * 1.2)
                        self.pattern_database[pattern_key] = {
                            'pattern': segment,
                            'probability': probability,
                            'strength': strength
                        }

    def model1(self):
        recent = self.history[-10:]
        if len(recent) < 4: return None
        patterns = []
        for k, v in self.pattern_database.items():
            p = v['pattern']
            if len(recent) < len(p): continue
            if recent[-len(p)+1:] == p[:-1]:
                patterns.append({'type': k, 'prediction': p[-1], 'probability': v['probability']})
        if not patterns: return None
        best = max(patterns, key=lambda x: x['probability'])
        conf = best['probability'] * 0.8
        if self.market_state['regime'] == 'trending': conf *= 1.1
        elif self.market_state['regime'] == 'volatile': conf *= 0.9
        return {'prediction': best['prediction'], 'confidence': min(0.95, conf), 'reason': f"Pattern {best['type']}"}

    def model2(self):
        short_term = self.history[-5:]
        long_term = self.history[-20:]
        if len(short_term) < 3 or len(long_term) < 10: return None
        st_t, st_x = short_term.count('T'), short_term.count('X')
        lt_t, lt_x = long_term.count('T'), long_term.count('X')
        st_trend = 'up' if st_t > st_x else 'down'
        lt_trend = 'up' if lt_t > lt_x else 'down'
        if st_trend == lt_trend:
            pred = 'T' if st_trend == 'up' else 'X'
            conf = 0.75
        else:
            pred = 'T' if lt_t > lt_x else 'X'
            conf = 0.6
        return {'prediction': pred, 'confidence': conf, 'reason': "Xu hướng đa khung"}

    def model3(self):
        recent = self.history[-12:]
        if len(recent) < 12: return None
        t_c, x_c = recent.count('T'), recent.count('X')
        diff = abs(t_c - x_c) / 12
        if diff < 0.4: return None
        return {'prediction': 'X' if t_c > x_c else 'T', 'confidence': min(0.95, diff * 0.8), 'reason': f"Cân bằng lệch long/short ({int(diff*100)}%)"}

    def model4(self):
        recent = self.history[-3:]
        if len(recent) < 3: return None
        if recent.count('T') == 3: return {'prediction': 'T', 'confidence': 0.7, 'reason': "Momentum Tăng mạnh"}
        if recent.count('X') == 3: return {'prediction': 'X', 'confidence': 0.7, 'reason': "Momentum Giảm mạnh"}
        return None

    def model5(self):
        preds = [self.model1(), self.model2(), self.model3(), self.model4()]
        valid = [p for p in preds if p]
        if len(valid) < 2: return None
        t_c = sum(1 for p in valid if p['prediction'] == 'T')
        x_c = sum(1 for p in valid if p['prediction'] == 'X')
        if abs(t_c - x_c) / len(valid) > 0.6:
            return {'prediction': 'X' if t_c > x_c else 'T', 'confidence': 0.65, 'reason': "Đảo chiều tỷ lệ đồng thuận cao"}
        return None

    def model6(self):
        if len(self.history) < 5: return None
        last_5 = self.history[-5:]
        if len(set(last_5)) == 1:
            return {'prediction': 'X' if last_5[0] == 'T' else 'T', 'confidence': 0.75, 'reason': "Bẻ cầu bệt dài 5 phiên"}
        return {'prediction': last_5[-1], 'confidence': 0.55, 'reason': "Thuận theo cầu ngắn"}

    def model7(self):
        return None

    def model8(self):
        if len(self.history) < 10: return None
        recent = self.history[-10:]
        changes = sum(1 for i in range(1, len(recent)) if recent[i] != recent[i-1])
        if changes / 9 > 0.7:
            return {'prediction': 'T' if recent[-1] == 'X' else 'X', 'confidence': 0.7, 'reason': "Cầu nhảy liên tục, bắt đảo chiều"}
        return None

    def model9(self):
        for name, p_data in self.advanced_patterns.items():
            if p_data['detect'](self.history):
                return {'prediction': p_data['predict'](self.history), 'confidence': p_data['confidence'], 'reason': p_data['description']}
        return None

    def model10(self):
        if len(self.history) < 15: return None
        recent = self.history[-15:]
        pt = recent.count('T') / 15
        px = recent.count('X') / 15
        entropy = 0
        if pt > 0: entropy -= pt * math.log2(pt)
        if px > 0: entropy -= px * math.log2(px)
        if entropy > 0.95:
            return {'prediction': 'T' if self.history[-1] == 'X' else 'X', 'confidence': 0.6, 'reason': "Entropy cực đại -> Dự kiến đảo chiều hồi sinh"}
        return None

    def model11(self):
        if len(self.history) < 4: return None
        if self.history[-4:] == ['T', 'T', 'X', 'X'] or self.history[-4:] == ['X', 'X', 'T', 'T']:
            return {'prediction': self.history[-1], 'confidence': 0.68, 'reason': "Cầu song song dập khuôn"}
        return None

    def model12(self):
        if len(self.history) < 6: return None
        if self.history[-6:] == ['T', 'X', 'T', 'X', 'T', 'X'] or self.history[-6:] == ['X', 'T', 'X', 'T', 'X', 'T']:
            return {'prediction': 'X' if self.history[-1] == 'T' else 'T', 'confidence': 0.72, 'reason': "Cầu 1-1 kéo dài"}
        return None

    def model13(self):
        if len(self.history) < 30: return None
        t_ratio = self.history[-30:].count('T') / 30
        if t_ratio > 0.65: return {'prediction': 'X', 'confidence': 0.68, 'reason': "Tài xuất hiện quá nhiều (>65%)"}
        if t_ratio < 0.35: return {'prediction': 'T', 'confidence': 0.68, 'reason': "Xỉu xuất hiện quá nhiều (<35%)"}
        return None

    def model14(self):
        if len(self.history) < 20: return None
        trans = self.session_stats['transitions']
        last = self.history[-1]
        to_t = trans.get(f"{last}toT", 0)
        to_x = trans.get(f"{last}toX", 0)
        if to_t + to_x == 0: return None
        prob_t = to_t / (to_t + to_x)
        if prob_t > 0.6: return {'prediction': 'T', 'confidence': prob_t, 'reason': "Ma trận Markov chuyển đổi nghiêng về Tài"}
        if prob_t < 0.4: return {'prediction': 'X', 'confidence': 1 - prob_t, 'reason': "Ma trận Markov chuyển đổi nghiêng về Xỉu"}
        return None

    def model15(self):
        if len(self.history) < 8: return None
        if self.history[-1] == 'T' and self.history[-3] == 'T' and self.history[-5] == 'T':
            return {'prediction': 'X', 'confidence': 0.62, 'reason': "Sóng Fibonacci lẻ chặn đỉnh"}
        return None

    def model16(self):
        if self.market_state['regime'] == 'volatile' and len(self.history) >= 4:
            return {'prediction': 'T' if self.history[-1] == 'X' else 'X', 'confidence': 0.65, 'reason': "Lọc nhiễu thị trường biến động mạnh"}
        return None

    def model17(self):
        if self.market_state['momentum'] > 0.8:
            return {'prediction': 'X', 'confidence': 0.6, 'reason': "Quá mua momentum -> Bẻ Xỉu"}
        if self.market_state['momentum'] < -0.8:
            return {'prediction': 'T', 'confidence': 0.6, 'reason': "Quá bán momentum -> Bẻ Tài"}
        return None

    def model18(self):
        if len(self.history) < 6: return None
        sub = self.history[-6:]
        if sub[0] == sub[5] and sub[1] == sub[4] and sub[2] == sub[3]:
            return {'prediction': 'T' if sub[-1] == 'X' else 'X', 'confidence': 0.7, 'reason': "Chuỗi đối xứng hoàn hảo hoàn tất"}
        return None

    def model19(self):
        if len(self.history) < 5: return None
        last_3 = self.history[-3:]
        t_c, x_c = 0, 0
        for i in range(len(self.history) - 4):
            if self.history[i:i+3] == last_3:
                next_val = self.history[i+3]
                if next_val == 'T': t_c += 1
                else: x_c += 1
        if t_c + x_c > 0 and max(t_c, x_c)/(t_c+x_c) > 0.7:
            return {'prediction': 'T' if t_c > x_c else 'X', 'confidence': max(t_c, x_c)/(t_c+x_c), 'reason': "N-gram lịch sử lặp lại"}
        return None

    def model20(self):
        if self.market_state['regime'] == 'trending':
            return {'prediction': 'T' if self.market_state['trend'] == 'up' else 'X', 'confidence': 0.75, 'reason': "Bám sát xu hướng thị trường đang Trending"}
        return None

    def model21(self):
        if len(self.history) < 2: return None
        return {'prediction': self.history[-1], 'confidence': 0.52, 'reason': "Mô hình phòng vệ quán tính gốc"}

    def get_all_predictions(self):
        preds = {}
        for i in range(1, 22):
            model_name = f"model{i}"
            method = getattr(self, model_name)
            try:
                res = method()
                if res and res.get('prediction'):
                    preds[model_name] = res
            except Exception:
                pass
        return preds

    def get_final_prediction(self):
        predictions = self.get_all_predictions()
        if not predictions:
            return None
            
        t_score = 0.0
        x_score = 0.0
        reasons = []
        
        for m_name, p in predictions.items():
            weight = self.weights.get(m_name, 1.0)
            score = p['confidence'] * weight
            if p['prediction'] == 'T':
                t_score += score
            elif p['prediction'] == 'X':
                x_score += score
            reasons.append(f"{m_name}: {p['prediction']} ({p['confidence']:.2f}) -> {p['reason']}")
            
        total_score = t_score + x_score
        if total_score == 0:
            return None
            
        final_pred = 'T' if t_score > x_score else 'X'
        confidence = max(t_score, x_score) / total_score
        
        return {
            'prediction': "Tài" if final_pred == 'T' else "Xỉu",
            'confidence': confidence * 100,
            'reasons': reasons
        }

global_system = UltraDicePredictionSystem()
latest_prediction_data = {"status": "Đang thu thập dữ liệu..."}

def background_prediction_worker():
    global latest_prediction_data
    api_url = "https://hitmd5-znas.onrender.com/api/taixiu"
    last_processed_phien = None
    
    print("[*] Luồng quét API ngầm đã bắt đầu...")
    while True:
        try:
            response = requests.get(api_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                ket_qua_raw = data.get("Ket_qua")
                phien_hien_tai = data.get("Phien")
                tong_diem = data.get("Tong")
                xx1 = data.get("Xuc_xac_1")
                xx2 = data.get("Xuc_xac_2")
                xx3 = data.get("Xuc_xac_3")
                
                char_result = 'T' if ket_qua_raw == "Tài" else 'X'
                
                if phien_hien_tai != last_processed_phien:
                    last_processed_phien = phien_hien_tai
                    
                    global_system.add_result(char_result)
                    prediction_result = global_system.get_final_prediction()
                    
                    if prediction_result:
                        latest_prediction_data = {
                            "phien_hien_tai": phien_hien_tai,
                            "ket_qua_hien_tai": ket_qua_raw,
                            "tong_diem": tong_diem,
                            "xuc_xac": [xx1, xx2, xx3],
                            "phien_ke_tiep": phien_hien_tai + 1,
                            "du_doan": prediction_result['prediction'],
                            "ty_le_tin_cay": f"{prediction_result['confidence']:.2f}%",
                            "ly_do": prediction_result['reasons']
                        }
                    else:
                        latest_prediction_data = {
                            "phien_hien_tai": phien_hien_tai,
                            "status": "Đang thu thập chuỗi dữ liệu..."
                        }
                    
                    print(f"\nPhiên: {phien_hien_tai} -> {ket_qua_raw} ({tong_diem}đ) [{xx1}-{xx2}-{xx3}]")
                    if prediction_result:
                        print(f"-> Dự đoán phiên {phien_hien_tai + 1}: Đặt {prediction_result['prediction']} ({prediction_result['confidence']:.2f}%)")
                    print("-" * 40)
            else:
                print(f"[!] Lỗi API: HTTP Code {response.status_code}")
        except Exception as e:
            print(f"[!] Lỗi kết nối luồng: {e}")
            
        time.sleep(5)

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        "status": "running",
        "message": "Ultra Dice Prediction System Server hoạt động bình thường.",
        "total_patterns_loaded": len(global_system.advanced_patterns)
    })

@app.route('/api/predict', methods=['GET'])
def get_prediction():
    return jsonify(latest_prediction_data)

if __name__ == "__main__":
    print("==========================================================")
    print("   HỆ THỐNG ULTRA DICE PREDICTION + WEB SERVER FLASK      ")
    print("==========================================================")
    
    worker_thread = threading.Thread(target=background_prediction_worker, daemon=True)
    worker_thread.start()
    
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)